"""Read a BOM CSV and show which catalogue part each line maps to.

Usage:  python scripts/check_bom.py [path/to/bom.csv]   (default: examples/sample_bom.csv)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bomwatch.bom import read_bom, match_bom
from bomwatch.catalog import load_ldos

path = sys.argv[1] if len(sys.argv) > 1 else "examples/sample_bom.csv"
lines = match_bom(read_bom(path), load_ldos())

for l in lines:
    where = ",".join(l["designators"]) or "-"
    print(f"line {l['line']}: {l['part']} x{l['quantity']} ({where})  ->  {l['match_type']}")
    for p in l["candidates"][:3]:
        print(f"      {p['lcsc']:<11} {p['part']:<18} {p['package'] or '?':<10} "
              f"stock {p['stock']:>7}   ${p['price']}")
    if len(l["candidates"]) > 3:
        print(f"      ... {len(l['candidates']) - 3} more")
