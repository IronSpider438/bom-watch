"""First connectivity test: list NVIDIA models on Nebius Token Factory and send one short prompt.

Reads NEBIUS_API_KEY from .env (never hard-code the key).
Run from the repo root:  python scripts/test_nemotron.py
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
key = os.environ.get("NEBIUS_API_KEY", "").strip()
if not key:
    raise SystemExit("NEBIUS_API_KEY is empty — paste your key into .env first.")

client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=key)

nvidia = sorted(m.id for m in client.models.list().data if "nvidia" in m.id.lower() or "nemotron" in m.id.lower())
print("NVIDIA / Nemotron models available:")
for mid in nvidia:
    print("  -", mid)
if not nvidia:
    raise SystemExit("No NVIDIA models found — check the model catalog in the dashboard.")

model = nvidia[0]
resp = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "In one sentence: what does an LDO voltage regulator do?"}],
    max_tokens=80,
)
print(f"\nTest call to {model}:")
print(resp.choices[0].message.content)
