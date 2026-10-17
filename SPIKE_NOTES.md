# BOM Watch — data spike notes (7 Oct 2026)

## Where the data lives
- jlcparts (MIT) publishes the JLCPCB/LCSC catalogue as static files on GitHub Pages.
- Manifest: `https://yaqwsx.github.io/jlcparts/data/manifest.json` (~2.9 MB) → list of categories, each with `shards` (gzipped JSONL) and an `attributesLut`.
- `index.json` does NOT exist (404) — always start from `manifest.json`.

## LDO category (our MVP)
- Category: `Power Management | Voltage Regulators - Linear, Low Drop Out (LDO) Regulators` — **1,119 parts**, 2 shards.
- Each shard line 1 = schema: `lcsc, mfr, joints, description, datasheet, price, img, url, attributes, stock, subcategory`.
- `price` = quantity tiers `[{qFrom, qTo, price}]` (USD).
- `stock` = integer. ✅ needed for monitoring.
- `attributes` = indices into `attributes-lut.json.gz` (46,605 entries); each decodes to **already-parsed numeric values with units**, e.g. Output Voltage 3.3 V, Output Current 1.0 A, Supply Voltage 15 V, Voltage Dropout 1.2 V @ 1 A, Package SOT-223.

## AMS1117-3.3 (demo part)
- 6 catalogue matches. Example: C18164485 "AMS1117-3.3", stock 51,091, $0.0397 @1, SOT-223, Vout 3.3 V, Iout 1 A, Vin max 15 V, dropout 1.2 V.

## Implications for the design
1. **Specs are already structured** → the code-based constraint checker can work directly on numbers. Nemotron's job shifts to: parsing messy user BOMs (part names → catalogue matches), understanding the user's use-case ("ESP32 board, 5 V USB in"), explaining substitutes and writing the alert.
2. **Data quality is imperfect** — e.g. C17702043 lists AMS1117 dropout as 0.012 V (real AMS1117 ≈ 1.1–1.3 V). Checker must flag implausible values instead of trusting them. Good demo point.
3. Stock/price monitoring = download the LDO shards daily, diff by `lcsc` id.

## Open
- Pinout is not in the catalogue → output "verify pinout in datasheet" (datasheet URL is available per part).
- How often jlcparts updates (GitHub Action) — check before relying on "daily".

## BOM matching (12 Oct 2026)
- LDO category now has 3 shards / 2,067 parts (was 1,119 on 7 Oct) — the catalogue grows; never hard-code counts.
- **Not every LCSC number is in jlcparts.** C6186 (the classic AMS1117-3.3 basic part) is missing from the snapshot. So matching falls back to the part name, narrowed by footprint (`SOT-223-3_TabPin2` → keeps SOT-223/SOT223, drops SOT-89/TO-252).
- Same name, several LCSC numbers (different manufacturers' clones) → reported as `ambiguous`, not silently picked.

## ⚠️ Stock data is not live (17 Oct 2026)
- Compared the cached LDO shards from 9 Oct and 17 Oct: **all 1,509 parts present on both days have identical stock numbers (0 changed)**, while 2,452 new parts were added (C6186 now present). The manifest is regenerated daily, but the stock field for existing parts does not move.
- Consequence: a daily jlcparts snapshot will almost never show a real stock-out. Specs/packages from jlcparts are still fine; **live stock/price needs another source** (e.g. LCSC's official API, which needs an application/key — check its terms) or must be stated as a limitation.
- For the hackathon demo, `scripts/demo_replay.py` replays a clearly-labelled **simulated** next day. Decision on the live-data source is open (Jayesh to decide).
