"""Glue: snapshot changes -> verified substitutes -> written alert.

    old snapshot + new snapshot --diff_snapshots--> change events
    each urgent event --find_substitutes--> parts that pass the hard checks (code)
    event + substitutes --write_alert--> human-readable alert (Nemotron)
"""
from .agent import write_alert, plausibility_flags
from .snapshot import diff_snapshots
from .substitutes import find_substitutes

# Events that need a replacement part. 'back_in_stock' is good news: reported, no substitutes.
NEEDS_SUBSTITUTE = {"out_of_stock", "missing", "low_stock", "price_up"}


def run(old_snap, new_snap, catalog, client=None):
    """Return one alert dict per change event, most urgent first."""
    by_lcsc = {p["lcsc"]: p for p in catalog}
    alerts = []
    for event in diff_snapshots(old_snap, new_snap):
        target = by_lcsc.get(event["lcsc"])
        if target is None:                       # part gone from the catalogue entirely
            target = {"lcsc": event["lcsc"], "part": event["part"]}
        subs = find_substitutes(target, catalog) if event["kind"] in NEEDS_SUBSTITUTE and "vout" in target else []
        text, source = write_alert(event, target, subs, client)
        alerts.append({
            "event": event,
            "target": target,
            "substitutes": subs[:3],
            "target_warnings": plausibility_flags(target) if "vout" in target else [],
            "alert": text,
            "written_by": source,
        })
    return alerts
