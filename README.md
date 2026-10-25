# BOM Watch

An AI agent that watches the stock and price of every part in an electronics bill of materials (BOM) and, when a part goes out of stock or jumps in price, proposes **code-verified drop-in substitutes**.

Built for the **Nebius × NVIDIA Global AI Hackathon** (Apps & Agents track) using an NVIDIA Nemotron model on Nebius Token Factory.

> Status: work in progress. Built with AI coding assistance (Claude); design decisions and verification by the author.

## Data
Component data comes from the open [jlcparts](https://github.com/yaqwsx/jlcparts) catalogue of JLCPCB/LCSC parts (MIT licence).

## How it works
1. **Read the BOM** (`bomwatch/bom.py`): CSV from KiCad / EasyEDA / JLCPCB, each line matched to the catalogue by LCSC number, then by part name + footprint.
2. **Snapshot + diff** (`bomwatch/snapshot.py`): today's stock and price per part, compared with the previous day → out of stock, missing, low stock, price jump, back in stock.
3. **Verified substitutes** (`bomwatch/substitutes.py`): plain code checks hard constraints (same output voltage and package; equal or better current, input voltage and dropout; in stock). No AI decides what is a valid part.
4. **Alert** (`bomwatch/agent.py`): NVIDIA Nemotron on Nebius Token Factory explains the verified substitutes in plain English, using only the facts the code passes it, and repeats data warnings (e.g. a catalogue dropout of 0.012 V for a 1 A LDO is flagged as implausible).

MVP scope: LDO voltage regulators.

## Known limitation: the demo's "next day" is simulated
The jlcparts stock field does not update day to day (0 of 1,509 parts changed over 8 days; see `SPIKE_NOTES.md`). The demo therefore replays a clearly labelled, hand-edited next day (one part sells out, one rises 35%). Everything after that is the real pipeline. A live source (e.g. LCSC's official API) would replace only the snapshot step.

## Run it
1. `cp .env.example .env` and paste your Nebius Token Factory key after `NEBIUS_API_KEY=`.
2. `pip install -r requirements.txt`
3. Command line: `python scripts/watch.py` (demo) or `python scripts/watch.py my_bom.csv --real` (daily real run).
4. Web app: `streamlit run app.py`. On Streamlit Cloud, put `NEBIUS_API_KEY` in the app's Secrets.

Without a key, alerts fall back to a plain template so the app still runs.

## Licence
MIT
