# app/services/finalize.py
import re
from typing import Optional
from app.models.schemas import FinalizeResponse

HASHTAGS = {
    "linkedin": ["#AI", "#EngineeringLeadership", "#Productivity", "#Learning"],
    "bluesky": ["#AI", "#buildinpublic"]
}

def _strip_inline_refs(text: str) -> str:
    # remove patterns like [1], [12], [a], [b]
    return re.sub(r"\s*\[(?:\d{1,2}|[A-Za-z])\]", "", text)

def _append_sources_line(text: str, platform: str, sources: Optional[str]) -> str:
    if not sources:
        return text
    domains = [d.strip() for d in sources.split(";") if d.strip()]
    if not domains:
        return text
    src_line = "Sources: " + "; ".join(dict.fromkeys(domains))  # de-dupe, preserve order
    # add if not already present
    if "Sources:" not in text:
        candidate = f"{text}\n\n{src_line}"
        max_len = 280 if platform.lower() == "bluesky" else 2800
        if len(candidate) <= max_len:
            return candidate
    return text

def finalize_text(text: str, platform: str, sources: Optional[str] = None) -> FinalizeResponse:
    max_len = 280 if platform.lower() == "bluesky" else 2800

    final_text = text.strip()
    final_text = _strip_inline_refs(final_text)
    final_text = _append_sources_line(final_text, platform, sources)

    # simple normalization: add 2 hashtags if not present
    tags = " ".join(HASHTAGS.get(platform.lower(), [])[:2])
    if len(final_text) + len(tags) + 2 <= max_len and tags not in final_text:
        final_text = f"{final_text}\n\n{tags}"

    # hard trim if needed
    if len(final_text) > max_len:
        final_text = final_text[: max_len - 1] + "…"

    return FinalizeResponse(final_text=final_text)
