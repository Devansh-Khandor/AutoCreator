# app/services/factcheck.py
import requests
from typing import List, Dict
import json
from app.config import settings
from openai import OpenAI

_oai = OpenAI(api_key=settings.openai_api_key)

def extract_claims(text: str, max_claims: int = 8) -> List[str]:
    """
    Use the LLM to pull out short factual claims that should be verified.
    Returns a list of strings.
    """
    prompt = f"""
You extract short factual claims (<= 15 words) that must be true in the real world.
- Claims should be atomic and concrete (dates, numbers, named facts, achievements).
- Ignore opinions, advice, and generic statements.
- Ignore any line beginning with "Sources:".
- Return a JSON OBJECT with this exact shape:
{{
  "items": ["claim 1", "claim 2", ...]
}}
If there are no factual claims, return {{"items":[]}}.
Extract up to {max_claims} claims.

TEXT:
\"\"\"{text}\"\"\"
"""

    resp = _oai.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        # keep object format to guarantee an object, not a bare list
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    try:
        data = json.loads(content)
        items = data.get("items", [])
    except Exception:
        items = []

    # normalize: strip, dedupe, filter empties
    uniq: List[str] = []
    seen = set()
    for c in items:
        c = (c or "").strip()
        if not c:
            continue
        if c.lower().startswith("sources:"):
            continue
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq

def serpapi_search(query: str, num: int = None) -> List[Dict]:
    """
    Minimal SerpApi Web Search call.
    Docs: https://serpapi.com/search-api
    """
    if not settings.serpapi_key:
        raise RuntimeError("Missing SERPAPI_KEY")

    url = "https://serpapi.com/search.json"
    params = {
        "engine": settings.serpapi_engine,  # e.g., google, duckduckgo, yahoo
        "q": query,
        "api_key": settings.serpapi_key,
        "location": settings.serpapi_location,
        "num": num or settings.serpapi_num,
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    results = []
    for item in (data.get("organic_results") or []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", "") or " ".join(item.get("snippet_highlighted_words", []) or []),
            "source": "serpapi",
        })

    if not results:
        for item in data.get("results", [])[: (num or settings.serpapi_num)]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link") or item.get("url", ""),
                "snippet": item.get("snippet", ""),
                "source": "serpapi",
            })
    return results[: (num or settings.serpapi_num)]

def score_confidence(claim: str, results: List[Dict]) -> float:
    """
    Tiny heuristic: higher if multiple snippets overlap claim terms.
    """
    claim_terms = {w.lower().strip(".,:;!?()[]'\"") for w in claim.split() if len(w) > 3}
    hits = 0
    for r in results:
        text = f"{r.get('title','')} {r.get('snippet','')}".lower()
        overlap = sum(1 for t in claim_terms if t in text)
        if overlap >= max(1, len(claim_terms)//4):
            hits += 1
    if hits >= 3: return 0.95
    if hits == 2: return 0.85
    if hits == 1: return 0.65
    return 0.4

def audit_text(text: str) -> List[Dict]:
    """
    Full audit: extract claims -> search -> confidence -> top sources
    """
    claims = extract_claims(text)
    audits = []
    for c in claims:
        res = serpapi_search(c, num=5)
        conf = score_confidence(c, res)
        audits.append({
            "claim": c,
            "confidence": round(conf, 2),
            "sources": res[:3],
        })
    return audits
