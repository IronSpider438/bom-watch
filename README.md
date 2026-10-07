# BOM Watch

An AI agent that watches the stock and price of every part in an electronics bill of materials (BOM) and, when a part goes out of stock or jumps in price, proposes **code-verified drop-in substitutes**.

Built for the **Nebius × NVIDIA Global AI Hackathon** (Apps & Agents track) using an NVIDIA Nemotron model on Nebius Token Factory.

> Status: work in progress. Built with AI coding assistance (Claude); design decisions and verification by the author.

## Data
Component data comes from the open [jlcparts](https://github.com/yaqwsx/jlcparts) catalogue of JLCPCB/LCSC parts (MIT licence).

## Setup
1. `cp .env.example .env` and paste your Nebius Token Factory key after `NEBIUS_API_KEY=`.
2. `pip install -r requirements.txt`

## Licence
MIT
