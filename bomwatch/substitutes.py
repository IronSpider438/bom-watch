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


def find_substitutes(target, catalog):
    # TODO: Jayesh writes this
    return []
