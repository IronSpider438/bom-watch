"""BOM Watch web demo (Streamlit).

Run locally:   streamlit run app.py
On Streamlit Cloud, put NEBIUS_API_KEY in the app's Secrets (never in the repo).
"""
import os
import tempfile

import pandas as pd
import streamlit as st

try:                                            # Streamlit Cloud secrets -> environment
    os.environ.setdefault("NEBIUS_API_KEY", st.secrets["NEBIUS_API_KEY"])
except Exception:
    pass

from bomwatch.bom import read_bom, match_bom
from bomwatch.catalog import load_ldos
from bomwatch.demo import simulate_next_day
from bomwatch.pipeline import run
from bomwatch.snapshot import take_snapshot

st.set_page_config(page_title="BOM Watch", page_icon="🔌", layout="wide")
st.title("🔌 BOM Watch")
st.caption("Watches every part in your bill of materials. When one sells out or jumps in price, "
           "code finds drop-in substitutes and NVIDIA Nemotron explains them.")


@st.cache_data(ttl=24 * 3600, show_spinner="Downloading the JLCPCB/LCSC LDO catalogue (jlcparts)...")
def catalog():
    return load_ldos()


uploaded = st.file_uploader("Upload a BOM (CSV from KiCad / EasyEDA / JLCPCB)", type="csv")
if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
        f.write(uploaded.getvalue())
    bom_path = f.name
else:
    bom_path = "examples/sample_bom.csv"
    st.info("No file uploaded: using the sample ESP32-board BOM.")

cat = catalog()
lines = match_bom(read_bom(bom_path), cat)

st.subheader("1 · Your BOM, matched to the catalogue")
st.dataframe(pd.DataFrame([{
    "line": l["line"], "part": l["part"], "designators": ", ".join(l["designators"]),
    "match": l["match_type"],
    "catalogue part": l["candidates"][0]["lcsc"] if l["match_type"] in ("lcsc", "name") else "",
    "stock": l["candidates"][0]["stock"] if l["match_type"] in ("lcsc", "name") else None,
} for l in lines]), hide_index=True, width="stretch")
st.caption("MVP covers LDO regulators only; other lines show as not_found and are not monitored.")

st.subheader("2 · Next day")
st.warning("**Simulated.** jlcparts stock numbers don't update day to day, so the demo replays a "
           "hand-edited next day: the first part sells out, the second rises 35% in price. "
           "Everything after that (diff, substitute checks, AI alert) is the real pipeline.")

if st.button("Run BOM Watch", type="primary"):
    today = take_snapshot(lines)
    with st.spinner("Checking substitutes and asking Nemotron to write the alerts..."):
        alerts = run(today, simulate_next_day(today), cat)
    st.subheader("3 · Alerts")
    if not alerts:
        st.success("No changes.")
    for a in alerts:
        e = a["event"]
        with st.container(border=True):
            st.markdown(f"**{e['part']}** (`{e['lcsc']}`) · `{e['kind']}` · {e['old']} → {e['new']}")
            for w in a["target_warnings"]:
                st.caption(f"⚠️ catalogue data: {w}")
            if a["substitutes"]:
                st.dataframe(pd.DataFrame(a["substitutes"])[
                    ["lcsc", "part", "manufacturer", "package", "vout", "iout_max", "vin_max",
                     "dropout", "stock", "price"]], hide_index=True, width="stretch")
            elif e["kind"] != "back_in_stock":
                st.caption("No catalogue part passed every drop-in check.")
            st.markdown(a["alert"])
            st.caption(f"Alert written by: {a['written_by']}")

st.divider()
st.caption("Data: jlcparts (MIT) · Model: NVIDIA Nemotron on Nebius Token Factory · "
           "Always confirm the pinout in the datasheet before swapping a part.")
