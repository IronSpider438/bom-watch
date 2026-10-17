"""Demo: take today's real snapshot, then replay a SIMULATED 'tomorrow' and show the alerts.

The simulated day is clearly fake: we copy today's snapshot and edit it by hand
(one part sold out, one price jump) so the demo works without waiting for a real stock-out.

Usage:  python scripts/demo_replay.py [path/to/bom.csv]
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bomwatch.bom import read_bom, match_bom
from bomwatch.catalog import load_ldos
from bomwatch.snapshot import take_snapshot, save_snapshot, diff_snapshots

bom_path = sys.argv[1] if len(sys.argv) > 1 else "examples/sample_bom.csv"
today = take_snapshot(match_bom(read_bom(bom_path), load_ldos()))
print("saved", save_snapshot(today, "demo-today"))
print(f"monitoring {len(today['parts'])} parts; not monitored: {[u['part'] for u in today['unmonitored']]}")

# --- simulated next day (FAKE data for the demo) ---
tomorrow = copy.deepcopy(today)
tomorrow["date"] = "simulated-next-day"
lcscs = list(tomorrow["parts"])
tomorrow["parts"][lcscs[0]]["stock"] = 0                                     # first part sells out
if len(lcscs) > 1:
    tomorrow["parts"][lcscs[1]]["price"] = round(tomorrow["parts"][lcscs[1]]["price"] * 1.35, 4)   # +35% price
print("saved", save_snapshot(tomorrow, "demo-simulated-next-day"))

print("\nCHANGES:")
for e in diff_snapshots(today, tomorrow):
    print(f"  [{e['kind']}] {e['part']} ({e['lcsc']}): {e['old']} -> {e['new']}")
