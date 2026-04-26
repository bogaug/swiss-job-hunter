"""
scraper.py – Ricerca offerte di lavoro in Svizzera via Adzuna API.

Adzuna è gratuita (250 req/giorno) — registrati su https://developer.adzuna.com
In assenza di API key, viene restituita una lista demo per test dell'interfaccia.
"""

import requests
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional
from html import unescape
import re

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Regioni svizzere
# ──────────────────────────────────────────────────────────────────────────────
REGIONS: dict[str, dict] = {
    "Svizzera Romanda": {"adzuna": "suisse romande", "label": "FR/GE/VD/VS/NE/JU"},
    "Ticino":           {"adzuna": "ticino",          "label": "TI"},
    "Zurigo":           {"adzuna": "zurich",           "label": "ZH"},
    "Berna":            {"adzuna": "bern",             "label": "BE"},
    "Basilea":          {"adzuna": "basel",            "label": "BS/BL"},
    "Svizzera Centrale":{"adzuna": "lucerne",          "label": "LU/UR/SZ/OW/NW/ZG"},
    "Svizzera Orientale":{"adzuna": "st. gallen",      "label": "SG/GR/AR/AI/GL/TG/SH"},
    "Tutta la Svizzera":{"adzuna": "",                 "label": "CH"},
}


@dataclass
class Job:
    title:         str
    company:       str
    location:      str
    url:           str
    source:        str
    job_id:        str = ""
    contract_type: str = ""
    posted_date:   str = ""
    description:   str = ""
    tags:          List[str] = field(default_factory=list)


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return unescape(text).strip()


# ──────────────────────────────────────────────────────────────────────────────
# Adzuna API
# ──────────────────────────────────────────────────────────────────────────────
def _search_adzuna(
    query: str,
    where: str,
    max_results: int,
    app_id: str,
    app_key: str,
) -> List[Job]:
    jobs: List[Job] = []
    params: dict = {
        "app_id":           app_id,
        "app_key":          app_key,
        "what":             query,
        "results_per_page": min(max_results, 50),
        "content-type":     "application/json",
    }
    if where:
        params["where"] = where

    try:
        r = requests.get(
            "https://api.adzuna.com/v1/api/jobs/ch/search/1",
            params=params,
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()

        if "exception" in data:
            raise ValueError(data["exception"])

        for item in data.get("results", []):
            jobs.append(Job(
                title=item.get("title", "—"),
                company=item.get("company", {}).get("display_name", "—"),
                location=item.get("location", {}).get("display_name", "—"),
                url=item.get("redirect_url", ""),
                source="Adzuna",
                job_id=str(item.get("id", "")),
                posted_date=item.get("created", "")[:10],
                description=_strip_html(item.get("description", "")),
                tags=item.get("category", {}).get("label", "").split(","),
            ))
    except requests.RequestException as e:
        raise ConnectionError(f"Adzuna non raggiungibile: {e}") from e
    except ValueError as e:
        raise ValueError(f"Adzuna errore risposta: {e}") from e

    logger.info("Adzuna: %d risultati", len(jobs))
    return jobs


# ──────────────────────────────────────────────────────────────────────────────
# Dati demo (quando non c'è API key)
# ──────────────────────────────────────────────────────────────────────────────
_DEMO_JOBS = [
    Job("Data Engineer (DEMO)", "Nestlé SA", "Lausanne, VD", "https://www.adzuna.ch",
        "demo", description="Pipeline ETL, Python, Spark, Azure Data Factory.", posted_date="2026-04-20"),
    Job("Data Analyst (DEMO)", "Swisscom AG", "Bern, BE", "https://www.adzuna.ch",
        "demo", description="SQL, Power BI, statistiche descrittive.", posted_date="2026-04-19"),
    Job("ML Engineer (DEMO)", "EPFL Innovation Park", "Lausanne, VD", "https://www.adzuna.ch",
        "demo", description="PyTorch, MLOps, scikit-learn, Docker.", posted_date="2026-04-18"),
    Job("Data Scientist (DEMO)", "UBS Group AG", "Genève, GE", "https://www.adzuna.ch",
        "demo", description="Modelli predittivi, Python, R, risk analytics.", posted_date="2026-04-17"),
    Job("BI Developer (DEMO)", "SBB CFF FFS", "Bern, BE", "https://www.adzuna.ch",
        "demo", description="Power BI, SQL Server, DAX, ETL.", posted_date="2026-04-16"),
]


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
def search_jobs(
    query: str,
    region_name: str,
    max_results: int = 20,
    sources: List[str] | None = None,          # non usato, mantenuto per compatibilità
    adzuna_app_id: str = "",
    adzuna_app_key: str = "",
) -> List[Job]:
    """
    Cerca offerte in Svizzera via Adzuna API.
    Se non ci sono credenziali, restituisce dati demo filtrati per query.
    """
    region_info = REGIONS.get(region_name, REGIONS["Svizzera Romanda"])

    if not adzuna_app_id or not adzuna_app_key:
        # Modalità demo — filtra per query
        q = query.lower()
        filtered = [j for j in _DEMO_JOBS if q in j.title.lower() or q in j.description.lower()]
        return (filtered or _DEMO_JOBS)[:max_results]

    return _search_adzuna(query, region_info["adzuna"], max_results,
                          adzuna_app_id, adzuna_app_key)


def get_job_detail(url: str) -> str:
    """Scarica il testo della descrizione da un URL di offerta."""
    from bs4 import BeautifulSoup
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        for selector in ["[class*='description']", "[class*='job-detail']", "article", "main"]:
            el = soup.select_one(selector)
            if el:
                return el.get_text(separator="\n", strip=True)[:3000]
        return soup.get_text(separator="\n", strip=True)[:2000]
    except Exception as e:
        logger.warning("get_job_detail error: %s", e)
        return ""
