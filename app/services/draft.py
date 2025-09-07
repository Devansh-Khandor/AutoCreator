# app/services/draft.py
from typing import List, Optional
import json
from openai import OpenAI
from openai import RateLimitError, APIStatusError
from app.config import settings
from app.models.schemas import Topic, DraftVariant

client = OpenAI(api_key=settings.openai_api_key)

STYLE_GUIDE = """Tone: crisp, helpful, optimistic. Avoid hype.
Structure: HOOK on first line, short paragraphs (<=2 sentences), 1 CTA line.
No false claims; prefer concrete examples and numbers.
Audience: engineering leaders & ambitious students.
"""

CTA_BANK = [
    "What’s your take?",
    "Would you try this?",
    "Save this for later.",
    "Share with a teammate."
]

LENGTH_RULES = {
    "short": "90–140 words",
    "medium": "140–220 words",
    "long": "220–350 words"
}

def _call_llm(prompt: str, model: str):
    # Some models only support default temperature; omit it.
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

def _build_prompt(
    topic: Topic,
    platform: str,
    n: int,
    mode: str,
    background: Optional[str],
    length: str,
    research_sources: Optional[List[dict]],
) -> str:
    # Build "research pack" block (optional)
    research_block = ""
    if research_sources:
        refs = []
        for i, s in enumerate(research_sources[:5], start=1):
            title = s.get("title", "")
            url = s.get("url", "")
            refs.append(f"[{i}] {title} — {url}")
        if refs:
            research_block = "RESEARCH PACK:\n" + "\n".join(refs)

    if mode == "personal":
        body_rules = f"""
Write {n} {platform} posts in first person using the C-C-A-R-L frame:
- Context → Challenge → Action → Result (with a number if possible) → Lesson.
Use the user BACKGROUND below as raw material.
Length: {LENGTH_RULES.get(length,'140–220 words')}.
End with 1 CTA from: {CTA_BANK}.
Avoid hyperbole; keep it grounded.
BACKGROUND:
{background or 'N/A'}
"""
    else:
        # Topical / Insight — facts required, but NO inline [1] markers
        body_rules = f"""
Write {n} {platform} posts that deliver practical insight on the topic.
Include 2–3 concrete, verifiable facts (numbers/dates/names). Use the RESEARCH PACK for grounding if provided.
Do NOT include bracketed citation markers like [1] or [2].
After the post body, add a single line that starts with "Sources:" followed by up to 3 concise domains (e.g., nasa.gov; jpl.nasa.gov; space.com). No extra commentary.
Length: {LENGTH_RULES.get(length,'140–220 words')}.
End with 1 CTA from: {CTA_BANK}.
Avoid hashtags for now.
"""

    prompt = f"""
Return ONLY valid JSON with key "items" -> list of variants.

You are an expert {platform} content writer.
Follow this STYLE_GUIDE:
{STYLE_GUIDE}

TOPIC: "{topic.title}"
ANGLE (optional): "{topic.angle or ''}"

{body_rules}

{research_block}

JSON shape:
{{
  "items": [
    {{"variant": 1, "text": "TEXT", "rationale": "WHY THIS WORKS"}},
    ...
  ]
}}
"""
    return prompt

def generate_variants(
    topic: Topic,
    platform: str,
    n: int = 3,
    mode: str = "topical",
    background: Optional[str] = None,
    length: str = "medium",
    research_sources: Optional[List[dict]] = None,
) -> List[DraftVariant]:
    prompt = _build_prompt(topic, platform, n, mode, background, length, research_sources)

    models_to_try = [settings.openai_model]
    fb = getattr(settings, "openai_fallback_model", None)
    if fb and fb not in models_to_try:
        models_to_try.append(fb)

    last_err = None
    for m in models_to_try:
        try:
            resp = _call_llm(prompt, m)
            content = resp.choices[0].message.content
            data = json.loads(content)
            items = data.get("items", [])
            variants: List[DraftVariant] = []
            for i, item in enumerate(items[:n], start=1):
                variants.append(DraftVariant(
                    variant=item.get("variant", i),
                    text=(item.get("text") or "").strip(),
                    rationale=item.get("rationale")
                ))
            if variants:
                return variants
        except (RateLimitError, APIStatusError) as e:
            last_err = e
            continue
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(
        f"Draft generation failed (models tried: {models_to_try}). Last error: {last_err}"
    )
