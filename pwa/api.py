"""
pwa/api.py – FastAPI backend per Swiss Job Hunter PWA (Android).
Avvio: uvicorn pwa.api:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os, sys, logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.scraper import search_jobs, REGIONS, Job
from modules.ai_generator import generate_cover_letter, generate_email_subject
from modules.email_sender import send_email, preview_email
from modules.tracker import (
    init_db, add_application, get_applications, get_application,
    update_application_status, delete_application,
    get_stats, get_status_history, export_to_csv, STATUS_OPTIONS,
)

init_db()
logging.basicConfig(level=logging.WARNING)

app = FastAPI(title="Swiss Job Hunter API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve PWA static files ────────────────────────────────────────────────────
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/manifest.json", include_in_schema=False)
async def manifest():
    return FileResponse(STATIC_DIR / "manifest.json")


@app.get("/sw.js", include_in_schema=False)
async def sw():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


# ─────────────────────────────────────────────────────────────────────────────
# SEARCH
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/search")
async def api_search(
    query:          str = Query(..., min_length=1),
    region:         str = Query("Svizzera Romanda"),
    max_results:    int = Query(20, ge=5, le=50),
    adzuna_app_id:  str = Query(""),
    adzuna_app_key: str = Query(""),
):
    app_id  = adzuna_app_id  or os.getenv("ADZUNA_APP_ID",  "")
    app_key = adzuna_app_key or os.getenv("ADZUNA_APP_KEY", "")
    jobs = search_jobs(query, region, max_results,
                       adzuna_app_id=app_id, adzuna_app_key=app_key)
    is_demo = not (app_id and app_key)
    return {
        "jobs":    [_job_to_dict(j) for j in jobs],
        "total":   len(jobs),
        "is_demo": is_demo,
    }


def _job_to_dict(j: Job) -> dict:
    return {
        "title":        j.title,
        "company":      j.company,
        "location":     j.location,
        "url":          j.url,
        "source":       j.source,
        "posted_date":  j.posted_date,
        "description":  j.description[:400] if j.description else "",
    }


@app.get("/api/regions")
async def api_regions():
    return [{"name": k, "label": v["label"]} for k, v in REGIONS.items()]


# ─────────────────────────────────────────────────────────────────────────────
# AI GENERATION
# ─────────────────────────────────────────────────────────────────────────────
class GenerateLetterRequest(BaseModel):
    job_title:       str
    company:         str
    location:        str = ""
    job_description: str = ""
    candidate_name:  str
    candidate_role:  str = ""
    candidate_skills:str = ""
    candidate_edu:   str = ""
    candidate_exp:   str = ""
    candidate_langs: str = "Italiano (madrelingua), Francese C1, Inglese C1"
    extra_notes:     str = ""
    language:        str = "Francese"
    model:           str = "llama-3.3-70b-versatile"
    api_key:         str = ""


@app.post("/api/generate-letter")
async def api_generate_letter(req: GenerateLetterRequest):
    key = req.api_key or os.getenv("GROQ_API_KEY", "")
    if not key:
        raise HTTPException(400, "Groq API key mancante")
    candidate = {
        "name":      req.candidate_name,
        "role":      req.candidate_role,
        "skills":    req.candidate_skills,
        "education": req.candidate_edu,
        "experience":req.candidate_exp,
        "languages": req.candidate_langs,
    }
    try:
        letter = generate_cover_letter(
            api_key=key,
            job_title=req.job_title,
            company=req.company,
            location=req.location,
            job_description=req.job_description,
            candidate=candidate,
            extra_notes=req.extra_notes,
            language=req.language,
            model=req.model,
        )
        return {"letter": letter}
    except Exception as e:
        raise HTTPException(500, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────────────────────────────────────
class SendEmailRequest(BaseModel):
    to_email:      str
    subject:       str
    body:          str
    smtp_host:     str = "smtp.gmail.com"
    smtp_port:     int = 587
    smtp_user:     str = ""
    smtp_password: str = ""
    sender_name:   str = ""


@app.post("/api/send-email")
async def api_send_email(req: SendEmailRequest):
    smtp_config = {
        "host":         req.smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port":         req.smtp_port or int(os.getenv("SMTP_PORT", 587)),
        "user":         req.smtp_user     or os.getenv("SMTP_USER", ""),
        "password":     req.smtp_password or os.getenv("SMTP_PASSWORD", ""),
        "sender_name":  req.sender_name,
        "sender_email": req.smtp_user     or os.getenv("SMTP_USER", ""),
    }
    ok, msg = send_email(smtp_config, req.to_email, req.subject, req.body)
    if not ok:
        raise HTTPException(500, msg)
    return {"message": msg}


# ─────────────────────────────────────────────────────────────────────────────
# TRACKER
# ─────────────────────────────────────────────────────────────────────────────
class ApplicationCreate(BaseModel):
    job_title:    str
    company:      str
    location:     str = ""
    url:          str = ""
    hr_email:     str = ""
    cover_letter: str = ""
    status:       str = "Inviata"
    notes:        str = ""


class StatusUpdate(BaseModel):
    status: str
    notes:  str = ""


@app.get("/api/applications")
async def api_get_applications(status: Optional[str] = None):
    filters = [status] if status else None
    return get_applications(filters)


@app.post("/api/applications")
async def api_create_application(req: ApplicationCreate):
    app_id = add_application(**req.model_dump())
    return {"id": app_id, "message": "Candidatura salvata"}


@app.patch("/api/applications/{app_id}/status")
async def api_update_status(app_id: int, req: StatusUpdate):
    app = get_application(app_id)
    if not app:
        raise HTTPException(404, "Candidatura non trovata")
    update_application_status(app_id, req.status, req.notes)
    return {"message": "Stato aggiornato"}


@app.delete("/api/applications/{app_id}")
async def api_delete_application(app_id: int):
    delete_application(app_id)
    return {"message": "Candidatura eliminata"}


@app.get("/api/applications/{app_id}/history")
async def api_get_history(app_id: int):
    return get_status_history(app_id)


@app.get("/api/stats")
async def api_stats():
    return get_stats()


@app.get("/api/statuses")
async def api_statuses():
    return STATUS_OPTIONS


@app.get("/api/export/csv")
async def api_export_csv():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(export_to_csv(), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=candidature.csv"})
