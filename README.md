# RAF AI Intelligence Engine v1

Compliance-first v1: CSV inputs + simple probabilistic model + static site + optional Discord webhook.

## What you get
- Import RAF events/bouts/odds/outcomes from CSV
- SQLite database for persistence
- Elo-style prediction model + confidence bands + edge vs odds
- Generates a static Astro site
- Optional Discord webhook notifications per event update
- GitHub Actions build + deploy to GitHub Pages

## Quick start (local)
1) Create venv + install deps:
   python -m venv .venv
   source .venv/bin/activate  (Windows: .venv\Scripts\activate)
   pip install -r requirements.txt

2) Fill CSVs in data/input (templates included)

3) Run pipeline (build DB + model outputs + site data):
   python -m raf_ai.pipeline

4) Build/run site:
   cd site
   npm install
   npm run dev

## Optional: Discord webhook
Set env var:
  DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

Pipeline will send a short event update message after generating outputs.

## Deploy (GitHub Pages)
- Push repo to GitHub
- In repo settings: Pages -> Build and deployment -> GitHub Actions
- Workflow will build and deploy on push to main.
