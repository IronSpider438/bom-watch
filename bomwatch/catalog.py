"""Load the JLCPCB/LCSC LDO-regulator catalogue from jlcparts into plain Python dicts.

Data source: https://yaqwsx.github.io/jlcparts (MIT). Files are downloaded once per day
into data/cache/ (gitignored) and reused after that.
"""
import gzip
import json
import urllib.request
from datetime import date
from pathlib import Path

BASE_URL = "https://yaqwsx.github.io/jlcparts/data/"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
LDO_SUBCATEGORY = "Low Drop Out (LDO)"


def _download(name):
    """Return the local path of a jlcparts file, downloading it if today's copy is missing."""
    day_dir = CACHE_DIR / date.today().isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)
    path = day_dir / name
    if not path.exists():
        with urllib.request.urlopen(BASE_URL + name, timeout=60) as resp:
            path.write_bytes(resp.read())
    return path


def _ldo_category(manifest):
    cats = manifest["categories"]
    for cat in (cats.values() if isinstance(cats, dict) else cats):
        for raw in cat.get("rawCategories", []):
            if LDO_SUBCATEGORY in raw.get("subcategory", ""):
                return cat
    raise LookupError("LDO category not found in jlcparts manifest")


def _attr(lut, attr_ids, name, key=None):
    """Value of one attribute (e.g. 'Output Voltage'), or None if the part doesn't list it."""
    for i in attr_ids:
        attr_name, spec = lut[i]
        if attr_name == name:
            values = spec["values"]
            field = key or spec.get("primary") or spec.get("default")
            return values[field][0] if field in values else None
    return None


def load_ldos():
    """Return every LDO in the catalogue as a list of dicts with numeric specs (SI units)."""
    manifest = json.loads(_download("manifest.json").read_text(encoding="utf-8"))
    lut = json.load(gzip.open(_download(manifest["attributesLut"]), "rt", encoding="utf-8"))
    parts = []
    for shard in _ldo_category(manifest)["shards"]:
        lines = gzip.open(_download(shard), "rt", encoding="utf-8").read().splitlines()
        col = json.loads(lines[0])
        for line in lines[1:]:
            row = json.loads(line)
            ids = row[col["attributes"]]
            prices = row[col["price"]] or []
            parts.append({
                "lcsc": row[col["lcsc"]],
                "part": row[col["mfr"]],
                "manufacturer": _attr(lut, ids, "Manufacturer"),
                "package": _attr(lut, ids, "Package"),
                "output_type": _attr(lut, ids, "Output Type"),          # "Fixed" / "Adjustable"
                "vout": _attr(lut, ids, "Output Voltage"),              # V
                "iout_max": _attr(lut, ids, "Output Current"),          # A
                "vin_max": _attr(lut, ids, "Supply Voltage"),           # V
                "dropout": _attr(lut, ids, "Voltage Dropout", "voltage"),  # V
                "dropout_at": _attr(lut, ids, "Voltage Dropout", "current"),  # A
                "status": _attr(lut, ids, "Status"),
                "basic": _attr(lut, ids, "Basic/Extended") == "Basic",
                "stock": row[col["stock"]],
                "price": prices[0]["price"] if prices else None,        # USD, smallest quantity tier
                "datasheet": row[col["datasheet"]],
                "description": row[col["description"]],
            })
    return parts
