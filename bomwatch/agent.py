"""The AI part of BOM Watch: Nemotron (on Nebius Token Factory) writes the alert.

Division of labour, on purpose:
  - CODE decides what is true: which part changed, which substitutes pass the hard
    constraints (substitutes.py), which catalogue values look implausible (below).
  - NEMOTRON only explains those facts to a human: why each substitute fits, what to
    double-check, what to do next. It is told to use ONLY the facts we give it, so it
    cannot invent a part or a spec.

If there is no API key (or the call fails), we fall back to a plain template alert,
so the demo still works offline.
"""
import json
import os

from dotenv import load_dotenv

MODEL = "nvidia/nemotron-3-super-120b-a12b"
BASE_URL = "https://api.tokenfactory.nebius.com/v1/"

EVENT_TEXT = {
    "out_of_stock": "went OUT OF STOCK",
    "missing": "DISAPPEARED from the catalogue",
    "low_stock": "is running LOW on stock",
    "price_up": "JUMPED in price",
    "back_in_stock": "is BACK in stock",
}


def plausibility_flags(part):
    """Return warnings about catalogue values that are probably wrong (empty list = looks fine).

    The catalogue is scraped data, so some specs are typos. Example we found: one AMS1117
    listed with 0.012 V dropout, while the real chip needs about 1.1-1.3 V.
    """
    flags = []
    d, vin, vout, iout = part.get("dropout"), part.get("vin_max"), part.get("vout"), part.get("iout_max")
    if d is not None and iout is not None and iout >= 0.5 and d < 0.05:
        flags.append(f"dropout {d} V is implausibly low for a {iout} A LDO - check the datasheet")
    if vin is not None and vout is not None and vin <= vout:
        flags.append(f"max input {vin} V is not above the output {vout} V - catalogue error?")
    for name in ("vout", "iout_max", "vin_max", "dropout"):
        if part.get(name) is None:
            flags.append(f"{name} not listed in the catalogue - confirm in the datasheet")
    return flags


def _facts(event, target, substitutes):
    """The structured facts we hand to the model (and to the fallback template)."""
    keep = ("lcsc", "part", "manufacturer", "package", "vout", "iout_max", "vin_max",
            "dropout", "stock", "price", "datasheet")
    pick = lambda p: {k: p.get(k) for k in keep}
    return {
        "event": {"kind": event["kind"], "old": event["old"], "new": event["new"]},
        "checks_applied_by_code": [
            f"output voltage == {target.get('vout')} V", f"package == {target.get('package')}",
            f"output current >= {target.get('iout_max')} A", f"max input voltage >= {target.get('vin_max')} V",
            f"dropout <= {target.get('dropout')} V", "stock > 0"],
        "original_part": pick(target) | {"warnings": plausibility_flags(target)},
        "verified_substitutes": [pick(s) | {"warnings": plausibility_flags(s)} for s in substitutes[:3]],
    }


def _template_alert(event, target, substitutes):
    lines = [f"{target['part']} ({target['lcsc']}) {EVENT_TEXT.get(event['kind'], event['kind'])}: "
             f"{event['old']} -> {event['new']}."]
    if not substitutes:
        lines.append("No catalogue part passed all the drop-in checks.")
    for s in substitutes[:3]:
        lines.append(f"- {s['part']} ({s['lcsc']}), {s['package']}, {s['iout_max']} A, "
                     f"Vin max {s['vin_max']} V, dropout {round(s['dropout'], 3)} V, ${s['price']}, stock {s['stock']}")
        lines += [f"    warning: {w}" for w in plausibility_flags(s)]
    lines.append("Always check the pinout in the datasheet before swapping.")
    return "\n".join(lines)


def _client():
    load_dotenv(".env")
    key = os.environ.get("NEBIUS_API_KEY", "").strip()
    if not key:
        return None
    from openai import OpenAI
    return OpenAI(base_url=BASE_URL, api_key=key)


SYSTEM = (
    "You are BOM Watch, an assistant for electronics engineers. You write short alerts about "
    "parts in a bill of materials. Use ONLY the facts in the JSON you are given: never invent "
    "parts, numbers or specs. The substitutes were already checked by code against the exact "
    "rules in 'checks_applied_by_code'; quote those rules exactly if you mention them. Explain in plain English why each one is a safe swap and how it differs "
    "(price, stock, margins). Repeat every warning. Always end by telling the engineer to confirm "
    "the PINOUT in the datasheet, because the catalogue does not list pinouts. Max 150 words. "
    "Write the alert once: one opening sentence, one bullet per substitute, one closing line. "
    "Never repeat a sentence or a bullet."
)


def write_alert(event, target, substitutes, client=None):
    """Return (alert_text, source) where source is the model name or 'template'."""
    client = client or _client()
    if client is None:
        return _template_alert(event, target, substitutes), "template"
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": json.dumps(_facts(event, target, substitutes))}],
            max_tokens=700,
            temperature=0.2,
            frequency_penalty=0.3,                  # stops the model looping on its own text
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        return resp.choices[0].message.content.strip(), MODEL
    except Exception as exc:                      # network/API trouble: the demo must not crash
        return _template_alert(event, target, substitutes) + f"\n(AI unavailable: {exc.__class__.__name__})", "template"
