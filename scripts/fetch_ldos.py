"""Download the LDO catalogue and show the AMS1117-3.3 entries (our demo part)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from bomwatch.catalog import load_ldos

parts = load_ldos()
print(f"{len(parts)} LDO regulators loaded")
print(f"{sum(p['stock'] > 0 for p in parts)} of them in stock\n")

for p in parts:
    if p["part"] and p["part"].upper().startswith("AMS1117-3.3"):
        print(f"{p['lcsc']:>12}  {p['part']:<16} {p['package']:<10} "
              f"Vout={p['vout']} V  Iout={p['iout_max']} A  Vin_max={p['vin_max']} V  "
              f"dropout={p['dropout']} V  stock={p['stock']}  ${p['price']}")
