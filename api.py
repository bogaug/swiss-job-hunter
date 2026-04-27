"""
api.py – FastAPI backend per Swiss Job Hunter PWA.

Avvio: uvicorn api:app --host 0.0.0.0 --port 8000 --reload

Endpoints:
  POST /api/search                     – cerca offerte
  POST /api/generate-letter            – genera lettera con AI
  POST /api/send-email                 – invia candidatura
  GET  /api/applications               – lista candidature
  POST /api/applications               – aggiungi candidatura
  PUT  /api/applications/{id}/status   – aggiorna stato
  DELETE /api/applications/{id}        – elimina
  GET  /api/stats                      – statistiche
  GET  /api/regions                    – lista regioni
  GET  /                               – serve la PWA
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import os
from pathlib import Path

from modules.scraper import search_jobs, REGIONS
from modules.ai_generator import generate_cover_letter, generate_email_subject
from modules.email_sender import send_email, test_email_config
from modules.tracker import (
    init_db, add_application, get_applications, get_application,
    update_application_status, delete_application, get_stats,
    export_to_csv, STATUS_OPTIONS,
)

logging.basicConfig(level=logging.WARNING)
init_db()

app = FastAPI(title="Swiss Job Hunter API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve PWA static files ────────────────────────────────────────────────────
PWA_DIR = Path(__file__).parent / "pwa"
app.mount("/pwa", StaticFiles(directory=str(PWA_DIR)), name="pwa")


@app.get("/")
async def root():
    return FileResponse(str(PWA_DIR / "index.html"))


# ──────────────────────────────────────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query:          str
    region:         str = "Svizzera Romanda"
    max_results:    int = 20
    adzuna_app_id:  str = ""
    adzuna_app_key: str = ""


class GenerateLetterRequest(BaseModel):
    groq_api_key:    str
    job_title:       str
    company:         str
    location:        str = ""
    job_description: str = ""
    candidate:       dict
    extra_notes:     str = ""
    language:        str = "Francese"
    model:           str = "llama-3.3-70b-versatile"


class SendEmailRequest(BaseModel):
    smtp_host:     str = "smtp.gmail.com"
    smtp_port:     int = 587
    smtp_user:     str
    smtp_password: str
    sender_name:   str = ""
    to_email:      str
    subject:       str
    body:          str


class AddApplicationRequest(BaseModel):
    job_title:    str
    company:      str
    location:     str = ""
    url:          str = ""
    hr_email:     str = ""
    cover_letter: str = ""
    status:       str = "Inviata"
    notes:        str = ""


class UpdateStatusRequest(BaseModel):
    status: str
    notes:  str = ""


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/api/regions")
async def get_regions():
    return [{"name": k, "label": v["label"]} for k, v in REGIONS.items()]


@app.get("/api/statuses")
async def get_statuses():
    return STATUS_OPTIONS


@app.post("/api/search")
async def search(req: SearchRequest):
    try:
        jobs = search_jobs(
            query=req.query,
            region_name=req.region,
            max_results=req.max_results,
            adzuna_app_id=req.adzuna_app_id,
            adzuna_app_key=req.adzuna_app_key,
        )
        is_demo = not (req.adzuna_app_id and req.adzuna_app_key)
        return {
            "jobs": [
                {
                    "title":        j.title,
                    "company":      j.company,
                    "location":     j.location,
                    "url":          j.url,
                    "source":       j.source,
                    "posted_date":  j.posted_date,
                    "description":  j.description,
                }
                for j in jobs
            ],
            "is_demo": is_demo,
            "count":   len(jobs),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-letter")
async def generate_letter(req: GenerateLetterRequest):
    if not req.groq_api_key:
        raise HTTPException(status_code=400, detail="Groq API key mancante")
    try:
        letter = generate_cover_letter(
            api_key=req.groq_api_key,
            job_title=req.job_title,
            company=req.company,
            location=req.location,
            job_description=req.job_description,
            candidate=req.candidate,
            extra_notes=req.extra_notes,
            language=req.language,
            model=req.model,
        )
        return {"letter": letter}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-subject")
async def generate_subject(req: GenerateLetterRequest):
    try:
        subject = generate_email_subject(
            req.groq_api_key,
            req.job_title,
            req.company,
            req.candidate.get("name", ""),
            req.language,
        )
        return {"subject": subject}
    except Exception as e:
        return {"subject": f"Candidatura – {req.job_title} | {req.candidate.get('name','')}"}


@app.post("/api/send-email")
async def send_email_endpoint(req: SendEmailRequest):
    smtp_config = {
        "host":         req.smtp_host,
        "port":         req.smtp_port,
        "user":         req.smtp_user,
        "password":     req.smtp_password,
        "sender_name":  req.sender_name,
        "sender_email": req.smtp_user,
    }
    ok, msg = send_email(
        smtp_config=smtp_config,
        to_email=req.to_email,
        subject=req.subject,
        body=req.body,
    )
    if ok:
        return {"success": True, "message": msg}
    raise HTTPException(status_code=500, detail=msg)


@app.post("/api/test-smtp")
async def test_smtp(req: SendEmailRequest):
    ok = test_email_config(req.smtp_host, req.smtp_port, req.smtp_user, req.smtp_password)
    return {"success": ok}


@app.get("/api/applications")
async def list_applications(status: Optional[str] = None):
    filters = [status] if status else None
    apps = get_applications(filters)
    return apps


@app.post("/api/applications")
async def create_application(req: AddApplicationRequest):
    app_id = add_application(
        job_title=req.job_title,
        company=req.company,
        location=req.location,
        url=req.url,
        hr_email=req.hr_email,
        cover_letter=req.cover_letter,
        status=req.status,
        notes=req.notes,
    )
    return {"id": app_id, "success": True}


@app.put("/api/applications/{app_id}/status")
async def update_status(app_id: int, req: UpdateStatusRequest):
    update_application_status(app_id, req.status, req.notes)
    return {"success": True}


@app.delete("/api/applications/{app_id}")
async def delete_app(app_id: int):
    delete_application(app_id)
    return {"success": True}


@app.get("/api/stats")
async def stats():
    return get_stats()


@app.get("/api/export/csv")
async def export_csv():
    from fastapi.responses import Response
    csv = export_to_csv()
    return Response(content=csv, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=candidature.csv"})
