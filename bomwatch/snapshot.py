"""Daily snapshots of a BOM's stock and price, and the diff between two snapshots.

A snapshot is a small JSON file (snapshots/<date>.json) that remembers, for every BOM
part we could match, how much stock there was and what it cost on that day. Comparing
today's snapshot with yesterday's tells us what changed: a part sold out, got cheaper,
jumped in price, and so on. Those changes are what BOM Watch alerts on.
"""
import json
from datetime import date
from pathlib import Path

SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "snapshots"

LOW_STOCK = 1000      # warn when stock falls below this many units
PRICE_JUMP = 0.20     # warn when the price rises by 20% or more


def take_snapshot(lines, day=None):
    """Turn matched BOM lines (from bom.match_bom) into a snapshot dict.

    Only lines with a definite match ('lcsc' or 'name') are monitored. 'ambiguous' and
    'not_found' lines are listed separately so the user knows they are NOT being watched.
    """
    parts, unmonitored = {}, []
    for line in lines:
        if line["match_type"] in ("lcsc", "name"):
            p = line["candidates"][0]
            parts[p["lcsc"]] = {
                "part": p["part"],
                "designators": line["designators"],
                "quantity": line["quantity"],
                "stock": p["stock"],
                "price": p["price"],
            }
        else:
            unmonitored.append({"line": line["line"], "part": line["part"], "reason": line["match_type"]})
    return {"date": (day or date.today()).isoformat(), "parts": parts, "unmonitored": unmonitored}


def save_snapshot(snap, name=None):
    """Write a snapshot to snapshots/<name or date>.json and return the path."""
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    path = SNAPSHOT_DIR / f"{name or snap['date']}.json"
    path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return path


def load_snapshot(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def diff_snapshots(old, new):
    """Compare two snapshots and return a list of change events (dicts).

    Each event has: lcsc, part, kind, old, new. Kinds:
      out_of_stock   stock went from >0 to 0                  (most urgent)
      missing        the part disappeared from the catalogue
      low_stock      stock dropped below LOW_STOCK
      price_up       price rose by PRICE_JUMP (20%) or more
      back_in_stock  stock went from 0 to >0                   (good news)
    """
    events = []
    for lcsc, was in old["parts"].items():
        now = new["parts"].get(lcsc)
        ev = lambda kind, a, b: events.append({"lcsc": lcsc, "part": was["part"], "kind": kind, "old": a, "new": b})
        if now is None:
            ev("missing", was["stock"], None)
            continue
        s0, s1 = was["stock"] or 0, now["stock"] or 0
        if s0 > 0 and s1 == 0:
            ev("out_of_stock", s0, s1)
        elif s0 == 0 and s1 > 0:
            ev("back_in_stock", s0, s1)
        elif s0 >= LOW_STOCK > s1:
            ev("low_stock", s0, s1)
        p0, p1 = was["price"], now["price"]
        if p0 and p1 and p1 >= p0 * (1 + PRICE_JUMP):
            ev("price_up", p0, p1)
    order = ["out_of_stock", "missing", "low_stock", "price_up", "back_in_stock"]
    return sorted(events, key=lambda e: order.index(e["kind"]))
