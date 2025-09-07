# app/main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from urllib.parse import urlparse

from app.models.schemas import (
    GenerateDraftRequest, GenerateDraftResponse, FinalizeRequest,
    FinalizeResponse, PublishRequest, PublishResponse, Topic
)
from app.services.draft import generate_variants
from app.services.finalize import finalize_text
from app.services.publish import publish_bluesky, export_linkedin_text
from app.services.factcheck import audit_text, serpapi_search

app = FastAPI(title="AutoCreator")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "variants": None})

@app.post("/ui/generate", response_class=HTMLResponse)
async def ui_generate(
    request: Request,
    topic: str = Form(...),
    angle: str = Form(""),
    platform: str = Form("linkedin"),
    post_type: str = Form("topical"),
    background: str = Form(""),
    length: str = Form("medium"),
    use_research: str = Form("0"),
):
    error = None
    variants = None
    sources_used = []        # always defined
    sources_domains = ""     # always defined

    try:
        if use_research == "1":
            q = f"{topic} {angle}".strip()
            sources_used = serpapi_search(q, num=5)  # top 5 results

            # build a de-duped "domain; domain; domain" string (max 3)
            domains: list[str] = []
            for s in sources_used:
                u = s.get("url", "")
                if not u:
                    continue
                d = urlparse(u).netloc.replace("www.", "")
                if d and d not in domains:
                    domains.append(d)
            sources_domains = "; ".join(domains[:3])

        variants = generate_variants(
            Topic(title=topic, angle=angle),
            platform,
            n=3,
            mode=post_type,
            background=background,
            length=length,
            research_sources=sources_used,
        )
    except Exception as e:
        error = str(e)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "variants": variants,
            "topic": topic,
            "angle": angle,
            "platform": platform,
            "error": error,
            "post_type": post_type,
            "background": background,
            "length": length,
            "sources_used": sources_used,
            "sources_domains": sources_domains,  # <-- important for finalizer
        },
    )


@app.post("/ui/finalize", response_class=HTMLResponse)
async def ui_finalize(
    request: Request,
    text: str = Form(...),
    platform: str = Form(...),
    sources: str = Form(""),
):
    fin = finalize_text(text, platform, sources or None)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "final_text": fin.final_text, "platform": platform},
    )


@app.post("/ui/factcheck", response_class=HTMLResponse)
async def ui_factcheck(request: Request, text: str = Form(...), platform: str = Form(...)):
    audits, error = [], None
    try:
        audits = audit_text(text)
    except Exception as e:
        error = str(e)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "audits": audits,
            "audit_count": len(audits),
            "fact_checked": True,
            "final_text": text,
            "platform": platform,
            "error": error
        },
    )

@app.post("/ui/publish/bluesky", response_class=HTMLResponse)
async def ui_publish_bsky(request: Request, text: str = Form(...)):
    res = publish_bluesky(text)
    return templates.TemplateResponse("index.html", {"request": request, "publish": res, "final_text": text, "platform": "bluesky"})

# Optional JSON APIs unchanged...
