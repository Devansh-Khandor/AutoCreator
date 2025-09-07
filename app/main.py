from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from urllib.parse import urlparse

from app.models.schemas import Topic, FinalizeResponse, PublishResponse
from app.services.draft import generate_variants
from app.services.finalize import finalize_text
from app.services.publish import publish_bluesky
from app.services.factcheck import audit_text, serpapi_search

app = FastAPI(title="AutoCreator")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ---------------------------
# Home
# ---------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# ===========================
# TOPIC FLOW
# ===========================
@app.get("/topic/new", response_class=HTMLResponse)
async def topic_new(request: Request):
    ctx = {
        "request": request,
        "platform": "linkedin",
        "length": "medium",
        "use_research": "1",
        "include_sources": "1",
        "variants": None,
    }
    return templates.TemplateResponse("topic.html", ctx)

@app.post("/topic/generate", response_class=HTMLResponse)
async def topic_generate(
    request: Request,
    topic: str = Form(...),
    angle: str = Form(""),
    platform: str = Form("linkedin"),
    length: str = Form("medium"),
    use_research: str = Form("0"),
    include_sources: str = Form("1"),
):
    error = None
    variants = None
    sources_used = []
    sources_domains = ""

    try:
        if use_research == "1":
            q = f"{topic} {angle}".strip()
            sources_used = serpapi_search(q, num=5)
            # Build de-duped domains string
            domains = []
            for s in sources_used:
                d = urlparse(s.get("url", "")).netloc.replace("www.", "")
                if d and d not in domains:
                    domains.append(d)
            sources_domains = "; ".join(domains[:3])

        variants = generate_variants(
            Topic(title=topic, angle=angle),
            platform=platform,
            n=3,
            mode="topical",
            background=None,
            length=length,
            research_sources=sources_used,
        )
    except Exception as e:
        error = str(e)

    ctx = {
        "request": request,
        "topic": topic,
        "angle": angle,
        "platform": platform,
        "length": length,
        "use_research": use_research,
        "include_sources": include_sources,
        "sources_used": sources_used,
        "sources_domains": sources_domains,
        "variants": variants,
        "error": error,
    }
    return templates.TemplateResponse("topic.html", ctx)

@app.post("/topic/factcheck", response_class=HTMLResponse)
async def topic_factcheck(
    request: Request,
    text: str = Form(...),
    platform: str = Form("linkedin"),
    topic: str = Form(""),
    angle: str = Form(""),
    length: str = Form("medium"),
    use_research: str = Form("0"),
    include_sources: str = Form("1"),
    sources_domains: str = Form(""),
):
    audits, error = [], None
    try:
        audits = audit_text(text)
    except Exception as e:
        error = str(e)

    ctx = {
        "request": request,
        "platform": platform,
        "topic": topic,
        "angle": angle,
        "length": length,
        "use_research": use_research,
        "include_sources": include_sources,
        "sources_domains": sources_domains,
        "final_text": text,
        "audits": audits,
        "audit_count": len(audits),
        "fact_checked": True,
        "error": error,
    }
    return templates.TemplateResponse("topic.html", ctx)

@app.post("/topic/finalize", response_class=HTMLResponse)
async def topic_finalize(
    request: Request,
    text: str = Form(...),
    platform: str = Form(...),
    include_sources: str = Form("1"),
    sources_domains: str = Form(""),
):
    fin = finalize_text(text, platform, sources_domains if include_sources == "1" else None)
    ctx = {"request": request, "final_text": fin.final_text, "platform": platform}
    return templates.TemplateResponse("topic.html", ctx)

@app.post("/topic/publish/bluesky", response_class=HTMLResponse)
async def topic_publish_bsky(request: Request, text: str = Form(...)):
    res = publish_bluesky(text)
    return templates.TemplateResponse("topic.html", {"request": request, "publish": res, "final_text": text, "platform": "bluesky"})

# ===========================
# PERSONAL FLOW
# ===========================
@app.get("/personal/new", response_class=HTMLResponse)
async def personal_new(request: Request):
    ctx = {
        "request": request,
        "platform": "linkedin",
        "length": "medium",
        "variants": None,
    }
    return templates.TemplateResponse("personal.html", ctx)

@app.post("/personal/generate", response_class=HTMLResponse)
async def personal_generate(
    request: Request,
    platform: str = Form("linkedin"),
    length: str = Form("medium"),
    role: str = Form(""),
    situation: str = Form(""),
    challenge: str = Form(""),
    action: str = Form(""),
    result: str = Form(""),
    lesson: str = Form(""),
    headline: str = Form(""),
):
    error = None
    variants = None

    # build background block from structured fields
    background_parts = []
    if role: background_parts.append(f"Role: {role}")
    if situation: background_parts.append(f"Context: {situation}")
    if challenge: background_parts.append(f"Challenge: {challenge}")
    if action: background_parts.append(f"Action: {action}")
    if result: background_parts.append(f"Result: {result}")
    if lesson: background_parts.append(f"Lesson: {lesson}")
    if headline: background_parts.append(f"Hook Hint: {headline}")
    background = "\n".join(background_parts) if background_parts else "N/A"

    try:
        # topic title is derived from headline or role/situation
        title = headline or f"{role} — {situation}".strip(" —")
        variants = generate_variants(
            Topic(title=title, angle=""),
            platform=platform,
            n=3,
            mode="personal",
            background=background,
            length=length,
            research_sources=None,
        )
    except Exception as e:
        error = str(e)

    ctx = {
        "request": request,
        "platform": platform,
        "length": length,
        "variants": variants,
        "error": error,
        "role": role,
        "situation": situation,
        "challenge": challenge,
        "action": action,
        "result": result,
        "lesson": lesson,
        "headline": headline,
    }
    return templates.TemplateResponse("personal.html", ctx)

@app.post("/personal/factcheck", response_class=HTMLResponse)
async def personal_factcheck(
    request: Request,
    text: str = Form(...),
    platform: str = Form("linkedin"),
):
    audits, error = [], None
    try:
        audits = audit_text(text)  # personal posts can still be fact-checked
    except Exception as e:
        error = str(e)

    ctx = {
        "request": request,
        "platform": platform,
        "final_text": text,
        "audits": audits,
        "audit_count": len(audits),
        "fact_checked": True,
        "error": error,
    }
    return templates.TemplateResponse("personal.html", ctx)

@app.post("/personal/finalize", response_class=HTMLResponse)
async def personal_finalize(
    request: Request,
    text: str = Form(...),
    platform: str = Form(...),
):
    fin = finalize_text(text, platform, None)  # no sources line for personal by default
    ctx = {"request": request, "final_text": fin.final_text, "platform": platform}
    return templates.TemplateResponse("personal.html", ctx)

@app.post("/personal/publish/bluesky", response_class=HTMLResponse)
async def personal_publish_bsky(request: Request, text: str = Form(...)):
    res = publish_bluesky(text)
    return templates.TemplateResponse("personal.html", {"request": request, "publish": res, "final_text": text, "platform": "bluesky"})
