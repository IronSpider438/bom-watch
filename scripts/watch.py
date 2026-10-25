"""One command for the whole loop: BOM -> snapshot -> changes -> substitutes -> alerts.

    python scripts/watch.py [bom.csv]           demo: today vs a SIMULATED next day
    python scripts/watch.py [bom.csv] --real    real: today vs the newest saved snapshot

Real mode saves today's snapshot, so running it once a day builds the history.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from bomwatch.bom import read_bom, match_bom
from bomwatch.catalog import load_ldos
from bomwatch.demo import simulate_next_day
from bomwatch.pipeline import run
from bomwatch.snapshot import SNAPSHOT_DIR, take_snapshot, save_snapshot, load_snapshot

args = [a for a in sys.argv[1:] if not a.startswith("--")]
bom_path = args[0] if args else "examples/sample_bom.csv"
catalog = load_ldos()
today = take_snapshot(match_bom(read_bom(bom_path), catalog))
print(f"Monitoring {len(today['parts'])} parts. Not monitored: {[u['part'] for u in today['unmonitored']]}")

if "--real" in sys.argv:
    history = sorted(p for p in SNAPSHOT_DIR.glob("20*.json") if p.stem != today["date"])
    save_snapshot(today)
    if not history:
        raise SystemExit("First snapshot saved. Run again tomorrow to see changes.")
    old, new = load_snapshot(history[-1]), today
    print(f"Comparing {old['date']} -> {new['date']}")
else:
    old, new = today, simulate_next_day(today)
    print("DEMO: comparing today -> a SIMULATED next day (first part sold out, second +35% price)")

alerts = run(old, new, catalog)
if not alerts:
    print("No changes.")
for a in alerts:
    e = a["event"]
    print("\n" + "=" * 70)
    print(f"[{e['kind']}] {e['part']} ({e['lcsc']}): {e['old']} -> {e['new']}")
    print(f"{len(a['substitutes'])} verified substitute(s) · alert written by {a['written_by']}")
    print("-" * 70)
    print(a["alert"])
