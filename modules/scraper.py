"""
scraper.py – Ricerca offerte su jobs.ch e jobup.ch
Strategia: prova l'endpoint __NEXT_DATA__ (Next.js), poi HTML parsing, poi API pubblica.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Regioni svizzere
# ──────────────────────────────────────────────────────────────────────────────
REGIONS: dict[str, dict] = {
    "Svizzera Romanda": {
        "jobup_region": "romandie",
        "jobs_region":  "romandie",
        "label": "FR/GE/VD/VS/NE/JU",
    },
    "Ticino": {
        "jobup_region": "ticino",
        "jobs_region":  "ticino",
        "label": "TI",
    },
    "Zurigo": {
        "jobup_region": "zurich",
        "jobs_region":  "zurich",
        "label": "ZH",
    },
    "Berna": {
        "jobup_region": "bern",
        "jobs_region":  "bern",
        "label": "BE",
    },
    "Basilea": {
        "jobup_region": "basel",
        "jobs_region":  "northwestern-switzerland",
        "label": "BS/BL",
    },
    "Svizzera Centrale": {
        "jobup_region": "central-switzerland",
        "jobs_region":  "central-switzerland",
        "label": "LU/UR/SZ/OW/NW/ZG",
    },
    "Svizzera Orientale": {
        "jobup_region": "eastern-switzerland",
        "jobs_region":  "eastern-switzerland",
        "label": "SG/GR/AR/AI/GL/TG/SH",
    },
    "Tutta la Svizzera": {
        "jobup_region": "",
        "jobs_region":  "",
        "label": "CH",
    },
}

LANG_TO_JOBUP = {
    "Svizzera Romanda": "fr",
    "Ticino":           "fr",   # jobup usa /fr anche per TI
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


# ──────────────────────────────────────────────────────────────────────────────
# Helpers HTTP
# ──────────────────────────────────────────────────────────────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
]


def _headers(accept_json: bool = False) -> dict:
    h = {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept-Language": "fr-CH,fr;q=0.9,it;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    }
    if accept_json:
        h["Accept"] = "application/json, */*;q=0.8"
    else:
        h["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    return h


def _get(url: str, params: dict | None = None, json_mode: bool = False,
         timeout: int = 12) -> Optional[requests.Response]:
    try:
        r = requests.get(url, params=params, headers=_headers(json_mode),
                         timeout=timeout)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        logger.warning("HTTP error %s: %s", url, e)
        return None


def _parse_next_data(html: str) -> Optional[dict]:
    """Estrae il JSON da __NEXT_DATA__ nei siti Next.js."""
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__")
    if tag and tag.string:
        try:
            return json.loads(tag.string)
        except json.JSONDecodeError:
            pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Jobup.ch
# ──────────────────────────────────────────────────────────────────────────────
def _jobup_api(query: str, region_code: str, max_results: int) -> List[Job]:
    """Prova l'API interna di jobup.ch (endpoint JSON)."""
    jobs: List[Job] = []
    url = "https://www.jobup.ch/api/search"
    params: dict = {
        "term":  query,
        "page":  1,
        "size":  min(max_results, 25),
    }
    if region_code:
        params["region"] = region_code

    r = _get(url, params=params, json_mode=True)
    if r is None:
        return jobs

    try:
        data = r.json()
        # jobup può restituire {"jobs": [...]} o {"data": {"jobs": [...]}}
        raw_jobs = (
            data.get("jobs")
            or data.get("data", {}).get("jobs")
            or []
        )
        for item in raw_jobs:
            job_url = item.get("url") or item.get("jobUrl") or ""
            if not job_url.startswith("http"):
                job_url = "https://www.jobup.ch" + job_url
            jobs.append(Job(
                title=item.get("title", "—"),
                company=item.get("companyName") or item.get("company", {}).get("name", "—"),
                location=item.get("place") or item.get("location", "—"),
                url=job_url,
                source="jobup.ch",
                job_id=str(item.get("id", "")),
                contract_type=item.get("employmentGradeFrom", ""),
                posted_date=item.get("publicationDate", "")[:10] if item.get("publicationDate") else "",
            ))
    except Exception as e:
        logger.warning("jobup API parse error: %s", e)

    return jobs


def _jobup_nextjs(query: str, region_code: str, max_results: int) -> List[Job]:
    """Fallback: parsing __NEXT_DATA__ dalla pagina HTML di jobup.ch."""
    jobs: List[Job] = []
    lang = "fr"  # jobup.ch usa /fr per romanda + ticino
    url = f"https://www.jobup.ch/{lang}/emplois/"
    params: dict = {"term": query}
    if region_code:
        params["region"] = region_code

    r = _get(url, params=params)
    if r is None:
        return jobs

    data = _parse_next_data(r.text)
    if not data:
        return jobs

    try:
        # Naviga la struttura Next.js
        page_props = data.get("props", {}).get("pageProps", {})
        raw_jobs = (
            page_props.get("jobs")
            or page_props.get("initialJobs")
            or page_props.get("searchResults", {}).get("jobs")
            or []
        )
        for item in raw_jobs[:max_results]:
            slug = item.get("slug") or item.get("url") or ""
            job_url = f"https://www.jobup.ch/{lang}/emplois/{slug}" if slug and not slug.startswith("http") else slug
            jobs.append(Job(
                title=item.get("title", "—"),
                company=item.get("companyName") or item.get("company", {}).get("name", "—"),
                location=item.get("place") or item.get("location", "—"),
                url=job_url,
                source="jobup.ch",
                job_id=str(item.get("id", "")),
                posted_date=str(item.get("publicationDate", ""))[:10],
            ))
    except Exception as e:
        logger.warning("jobup __NEXT_DATA__ parse error: %s", e)

    return jobs


def _jobup_html(query: str, region_code: str, max_results: int) -> List[Job]:
    """Ultimo fallback: CSS selectors sull'HTML di jobup.ch."""
    jobs: List[Job] = []
    url = "https://www.jobup.ch/fr/emplois/"
    params: dict = {"term": query}
    if region_code:
        params["region"] = region_code

    r = _get(url, params=params)
    if r is None:
        return jobs

    soup = BeautifulSoup(r.text, "html.parser")
    cards = (
        soup.select("article[data-cy='job-item']")
        or soup.select("li.ResultList_item__")
        or soup.select("[class*='JobItem']")
        or soup.select("article")
    )

    for card in cards[:max_results]:
        try:
            title_tag = card.select_one("h2, h3, [data-cy='job-title']")
            company_tag = card.select_one("[data-cy='company-name'], .company, span[class*='Company']")
            location_tag = card.select_one("[data-cy='location'], .location, span[class*='Place']")
            link_tag = card.select_one("a[href]")

            if not title_tag:
                continue

            raw_href = link_tag["href"] if link_tag else ""
            job_url = raw_href if raw_href.startswith("http") else "https://www.jobup.ch" + raw_href

            jobs.append(Job(
                title=title_tag.get_text(strip=True),
                company=company_tag.get_text(strip=True) if company_tag else "—",
                location=location_tag.get_text(strip=True) if location_tag else "—",
                url=job_url,
                source="jobup.ch",
            ))
        except Exception:
            continue

    return jobs


def search_jobup(query: str, region_code: str, max_results: int = 20) -> List[Job]:
    """Cerca su jobup.ch provando più strategie."""
    # 1) API interna
    jobs = _jobup_api(query, region_code, max_results)
    if jobs:
        logger.info("jobup API: %d risultati", len(jobs))
        return jobs

    time.sleep(0.8)

    # 2) __NEXT_DATA__
    jobs = _jobup_nextjs(query, region_code, max_results)
    if jobs:
        logger.info("jobup __NEXT_DATA__: %d risultati", len(jobs))
        return jobs

    time.sleep(0.8)

    # 3) HTML parsing
    jobs = _jobup_html(query, region_code, max_results)
    logger.info("jobup HTML: %d risultati", len(jobs))
    return jobs


# ──────────────────────────────────────────────────────────────────────────────
# Jobs.ch
# ──────────────────────────────────────────────────────────────────────────────
def _jobsch_api(query: str, region_code: str, max_results: int) -> List[Job]:
    """Prova l'endpoint JSON pubblico di jobs.ch."""
    jobs: List[Job] = []
    url = "https://api.jobs.ch/public-api/v1/jobs"
    params: dict = {
        "query":    query,
        "pageSize": min(max_results, 20),
        "page":     1,
    }
    if region_code:
        params["region"] = region_code

    r = _get(url, params=params, json_mode=True)
    if r is None:
        return jobs

    try:
        data = r.json()
        raw_jobs = data.get("hits") or data.get("jobs") or []
        for item in raw_jobs:
            slug = item.get("slug") or item.get("id", "")
            job_url = f"https://www.jobs.ch/fr/vacances-emplois/{slug}" if slug else "https://www.jobs.ch"
            jobs.append(Job(
                title=item.get("title", "—"),
                company=item.get("company", {}).get("name", "—") if isinstance(item.get("company"), dict) else str(item.get("company", "—")),
                location=item.get("location") or item.get("place") or "—",
                url=job_url,
                source="jobs.ch",
                job_id=str(item.get("id", "")),
                posted_date=str(item.get("publishedAt", ""))[:10],
            ))
    except Exception as e:
        logger.warning("jobs.ch API parse error: %s", e)

    return jobs


def _jobsch_html(query: str, region_code: str, max_results: int) -> List[Job]:
    """Fallback HTML per jobs.ch."""
    jobs: List[Job] = []
    url = "https://www.jobs.ch/fr/offres-d-emploi/"
    params: dict = {"term": query}
    if region_code:
        params["region"] = region_code

    r = _get(url, params=params)
    if r is None:
        return jobs

    # Prova anche __NEXT_DATA__
    data = _parse_next_data(r.text)
    if data:
        try:
            page_props = data.get("props", {}).get("pageProps", {})
            raw_jobs = (
                page_props.get("jobs")
                or page_props.get("initialJobList")
                or []
            )
            for item in raw_jobs[:max_results]:
                slug = item.get("slug") or item.get("id", "")
                job_url = f"https://www.jobs.ch/fr/offres-d-emploi/{slug}" if slug else "https://www.jobs.ch"
                jobs.append(Job(
                    title=item.get("title", "—"),
                    company=item.get("company", {}).get("name", "—") if isinstance(item.get("company"), dict) else "—",
                    location=item.get("place") or item.get("location", "—"),
                    url=job_url,
                    source="jobs.ch",
                ))
            if jobs:
                return jobs
        except Exception:
            pass

    # CSS parsing
    soup = BeautifulSoup(r.text, "html.parser")
    cards = (
        soup.select("[data-cy='job-card']")
        or soup.select("article[class*='JobCard']")
        or soup.select("li[class*='job']")
    )
    for card in cards[:max_results]:
        try:
            title_tag = card.select_one("h2, h3, [data-cy='job-title']")
            company_tag = card.select_one("[data-cy='company'], span[class*='company']")
            location_tag = card.select_one("[data-cy='location'], span[class*='location']")
            link_tag = card.select_one("a[href]")
            if not title_tag:
                continue
            raw_href = link_tag["href"] if link_tag else ""
            job_url = raw_href if raw_href.startswith("http") else "https://www.jobs.ch" + raw_href
            jobs.append(Job(
                title=title_tag.get_text(strip=True),
                company=company_tag.get_text(strip=True) if company_tag else "—",
                location=location_tag.get_text(strip=True) if location_tag else "—",
                url=job_url,
                source="jobs.ch",
            ))
        except Exception:
            continue

    return jobs


def search_jobsch(query: str, region_code: str, max_results: int = 20) -> List[Job]:
    jobs = _jobsch_api(query, region_code, max_results)
    if jobs:
        return jobs
    time.sleep(0.8)
    return _jobsch_html(query, region_code, max_results)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
def search_jobs(query: str, region_name: str, max_results: int = 20,
                sources: List[str] | None = None) -> List[Job]:
    """
    Cerca offerte di lavoro in Svizzera.

    Args:
        query:       Parole chiave (es: "Data Engineer Python")
        region_name: Nome regione da REGIONS (es: "Svizzera Romanda")
        max_results: Numero massimo di risultati totali
        sources:     ["jobup", "jobs.ch"] — default entrambi

    Returns:
        Lista di Job, deduplicata per URL.
    """
    if sources is None:
        sources = ["jobup", "jobs.ch"]

    region_info = REGIONS.get(region_name, REGIONS["Svizzera Romanda"])
    all_jobs: List[Job] = []
    seen_urls: set[str] = set()
    per_source = max(max_results // len(sources), 10)

    if "jobup" in sources:
        try:
            jobs = search_jobup(query, region_info["jobup_region"], per_source)
            for j in jobs:
                if j.url not in seen_urls:
                    seen_urls.add(j.url)
                    all_jobs.append(j)
        except Exception as e:
            logger.error("jobup search failed: %s", e)

    if "jobs.ch" in sources:
        time.sleep(1.2)
        try:
            jobs = search_jobsch(query, region_info["jobs_region"], per_source)
            for j in jobs:
                if j.url not in seen_urls:
                    seen_urls.add(j.url)
                    all_jobs.append(j)
        except Exception as e:
            logger.error("jobs.ch search failed: %s", e)

    return all_jobs[:max_results]


def get_job_detail(url: str) -> str:
    """Scarica e restituisce il testo della descrizione di un'offerta."""
    r = _get(url)
    if r is None:
        return ""
    soup = BeautifulSoup(r.text, "html.parser")
    # Rimuovi script e style
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    # Cerca sezione descrizione
    for selector in ["[class*='description']", "[class*='job-detail']",
                     "article", "main", ".content"]:
        el = soup.select_one(selector)
        if el:
            return el.get_text(separator="\n", strip=True)[:3000]
    return soup.get_text(separator="\n", strip=True)[:2000]
