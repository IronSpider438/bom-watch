"""Find substitutes for the AMS1117-3.3 (LCSC C18164485) and print them."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from bomwatch.catalog import load_ldos
from bomwatch.substitutes import find_substitutes

catalog = load_ldos()
target = next(p for p in catalog if p["lcsc"] == "C18164485")
print(f"Target: {target['part']} ({target['lcsc']}), {target['package']}, "
      f"{target['vout']} V, {target['iout_max']} A, dropout {target['dropout']} V, ${target['price']}\n")

subs = find_substitutes(target, catalog)
print(f"{len(subs)} substitutes found")
for p in subs[:15]:
    print(f"{p['lcsc']:>12}  {p['part']:<22} {p['package']:<10} {p['iout_max']} A  "
          f"dropout {p['dropout']} V  stock {p['stock']:>7}  ${p['price']}")
