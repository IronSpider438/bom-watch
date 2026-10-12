"""Read a BOM (bill of materials) CSV and match each line to a part in the catalogue.

A BOM is the shopping list for a circuit board: one row per part type, saying which
part it is, how many are needed and where they go on the board (designators like R1, U2).
Different tools (KiCad, EasyEDA, JLCPCB) name the columns differently, so we look for
several possible header names for each column.
"""
import csv
import re

# For each field we need, the header names different BOM exports use (compared in lowercase).
HEADER_ALIASES = {
    "lcsc": ["lcsc", "lcsc part", "lcsc part #", "lcsc part number", "jlcpcb part #", "supplier part"],
    "part": ["mpn", "manufacturer part", "manufacturer part number", "part number", "comment", "value"],
    "designator": ["designator", "reference", "references", "ref"],
    "quantity": ["quantity", "qty"],
    "footprint": ["footprint", "package"],
}
LCSC_RE = re.compile(r"^C\d+$")          # LCSC numbers look like C18164485


def _squash(text):
    """'SOT-223' and 'SOT223' -> 'SOT223', so different spellings compare equal."""
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def _find_columns(headers):
    """Map each field name (lcsc, part, ...) to the CSV header that holds it, or None."""
    lower = {h.strip().lower(): h for h in headers}
    return {field: next((lower[a] for a in aliases if a in lower), None)
            for field, aliases in HEADER_ALIASES.items()}


def read_bom(path):
    """Return the BOM as a list of dicts: line, part, lcsc, designators, quantity, footprint."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = _find_columns(reader.fieldnames or [])
        if not cols["part"] and not cols["lcsc"]:
            raise ValueError(f"No part-name or LCSC column found. Headers: {reader.fieldnames}")
        lines = []
        for n, row in enumerate(reader, start=2):        # line 1 is the header
            get = lambda field: (row.get(cols[field]) or "").strip() if cols[field] else ""
            designators = [d.strip() for d in get("designator").split(",") if d.strip()]
            qty = get("quantity")
            lcsc = get("lcsc").upper()
            lines.append({
                "line": n,
                "part": get("part"),
                "lcsc": lcsc if LCSC_RE.match(lcsc) else "",
                "designators": designators,
                "quantity": int(qty) if qty.isdigit() else len(designators),
                "footprint": get("footprint"),
            })
    return lines


def match_bom(lines, catalog):
    """Attach a catalogue match to every BOM line.

    Adds two keys to each line:
      match_type  'lcsc'       - the LCSC number was found in the catalogue (most reliable)
                  'name'       - no usable LCSC number, but exactly one part has this name
                  'ambiguous'  - several parts share this name; see 'candidates'
                  'not_found'  - nothing matched (or the part is outside our LDO catalogue)
      candidates  list of matching catalogue parts, highest stock first
    """
    by_lcsc = {p["lcsc"]: p for p in catalog}
    by_name = {}
    for p in catalog:
        by_name.setdefault(_squash(p["part"]), []).append(p)

    for line in lines:
        if line["lcsc"] in by_lcsc:
            line["match_type"], line["candidates"] = "lcsc", [by_lcsc[line["lcsc"]]]
            continue
        found = by_name.get(_squash(line["part"]), [])
        # Several manufacturers sell the same part name in different packages:
        # keep only the ones whose package appears in the BOM's footprint text.
        fp = _squash(line["footprint"])
        if fp and len(found) > 1:
            same_pkg = [p for p in found if p["package"] and _squash(p["package"]) in fp]
            found = same_pkg or found
        found = sorted(found, key=lambda p: p["stock"] or 0, reverse=True)
        line["candidates"] = found
        line["match_type"] = ("not_found" if not found else
                              "name" if len(found) == 1 else "ambiguous")
    return lines
