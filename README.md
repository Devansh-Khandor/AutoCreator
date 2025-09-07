# AutoCreator — AI Content Agent

FastAPI app that generates LinkedIn/Bluesky posts, runs a fact-check with web sources, and can publish to Bluesky.

## Features
- Draft generator (Topical or Personal; Short/Medium/Long)
- Optional research pack (SerpApi web results)
- Fact-check panel (claim extraction + sources + confidence)
- Finalizer (cleans refs, optional “Sources:” line, hashtags)
- Publish to Bluesky / Copy for LinkedIn

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in keys
uvicorn app.main:app --reload
Open http://127.0.0.1:8000
