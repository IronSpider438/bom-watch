"""Take today's real snapshot of a BOM and compare it with the most recent earlier one.

Run once a day (by hand for now; later a scheduler).
Usage:  python scripts/take_snapshot.py [path/to/bom.csv]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bomwatch.bom import read_bom, match_bom
from bomwatch.catalog import load_ldos
from bomwatch.snapshot import SNAPSHOT_DIR, take_snapshot, save_snapshot, load_snapshot, diff_snapshots

bom_path = sys.argv[1] if len(sys.argv) > 1 else "examples/sample_bom.csv"
snap = take_snapshot(match_bom(read_bom(bom_path), load_ldos()))

# earlier real snapshots are named by date (YYYY-MM-DD.json); skip demo files
earlier = sorted(p for p in SNAPSHOT_DIR.glob("20*.json") if p.stem < snap["date"]) if SNAPSHOT_DIR.exists() else []
print("saved", save_snapshot(snap))
if not earlier:
    print("first snapshot — nothing to compare yet")
else:
    events = diff_snapshots(load_snapshot(earlier[-1]), snap)
    print(f"compared with {earlier[-1].name}: {len(events)} change(s)")
    for e in events:
        print(f"  [{e['kind']}] {e['part']} ({e['lcsc']}): {e['old']} -> {e['new']}")
