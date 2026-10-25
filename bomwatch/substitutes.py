"""Substitute checker: given an LDO, find catalogue parts that can safely replace it.

YOUR PART (Jayesh). Write find_substitutes() below. Each part is a dict from
bomwatch.catalog.load_ldos(), with keys:
    lcsc, part, manufacturer, package, output_type, vout, iout_max, vin_max,
    dropout, dropout_at, status, basic, stock, price, datasheet, description
Any spec can be None if the catalogue doesn't list it.

A candidate is a valid substitute for `target` only if ALL of these hold:
    1. same output voltage (vout)
    2. same package, so it fits the same PCB footprint
       (careful: the data writes both "SOT-223" and "SOT223")
    3. output current  >= target's  (iout_max)
    4. max input voltage >= target's (vin_max)
    5. dropout <= target's (lower dropout is better)
    6. in stock (stock > 0)
    7. not the target itself (different lcsc)

Return the valid candidates sorted by price, cheapest first.
""" 
from .agent import plausibility_flags
def clean(pkg):
    return (pkg or "").replace("-", "").upper()
def find_substitutes(target, catalog):
    result = []
    for p in catalog:
        # rule 7: skip the target itself
        if p["lcsc"] == target["lcsc"]:
            continue
        # rule 6: in stock
        if not p["stock"]:
            continue
        # rule 1: same output voltage
        if p["vout"] !=target["vout"] :
            continue
        # rule 2: same package (SOT-223 == SOT223)
        if clean(p["package"]) != clean(target["package"]):
            continue
        # rule 3: output current >= target's
        if p["iout_max"] is None or p["iout_max"] < target["iout_max"]:
            continue
        # rule 4: max input voltage >= target's
        if p["vin_max"] is None or p["vin_max"] < target["vin_max"]:
            continue
        # rule 5: dropout <= target's
        if p["dropout"] is None or p["dropout"] > target["dropout"]:
            continue
        # rule 8: don't trust parts with impossible catalouge data
        if plausibility_flags(p):
            continue
        result.append(p)        # survived every rule
    result.sort(key=lambda p: p["price"] or 999)
    return result