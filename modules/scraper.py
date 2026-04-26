"""
scraper.py – Ricerca offerte di lavoro in Svizzera.

Strategia (in ordine di priorità):
1. RSS feed di jobs.ch  (nessuna API key, funziona sempre)
2. RSS feed di jobup.ch (nessuna API key, funziona sempre)
3. Adzuna API           (gratuita, 250 req/giorno — https://developer.adzuna.com)
"""

import requests
import xml.etree.ElementTree as ET
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional
from html import unescape
import re

logger = logging.getLogger(__name__)

REGIONS: dict[str, dict] = {
    "Svizzera Romanda": {
        "adzuna":    "suisse romande",
        "jobs_rss":  "romandie",
        "jobup_rss": "romandie",
        "label":     "FR/GE/VD/VS/NE/JU",
    },
    "Ticino": {
        "adzuna":    "ticino",
        "jobs_rss":  "ticino",
        "jobup_rss": "ticino",
        "label":     "TI",
    },
    "Zurigo": {
        "adzuna":    "zurich",
        "jobs_rss":  "zurich",
        "jobup_rss": "zurich",
        "label":     "ZH",
    },
    "Berna": {
        "adzuna":    "bern",
        "jobs_rss":  "bern",
        "jobup_rss": "bern",
        "label":     "BE",
    },
    "Basilea": {
        "adzuna":    "basel",
        "jobs_rss":  "northwestern-switzerland",
        "jobup_rss": "basel",
        "label":     "BS/BL",
    },
    "Svizzera Centrale": {
        "adzuna":    "central switzerland",
        "jobs_rss":  "central-switzerland",
        "jobup_rss": "central-switzerland",
        "label":     "LU/UR/SZ/OW/NW/ZG",
    },
    "Svizzera Orientale": {
        "adzuna":    "eastern switzerland",
        "jobs_rss":  "eastern-switzerland",
        "jobup_rss": "eastern-switzerland",
        "label":     "SG/GR/AR/AI/GL/TG/SH",
    },
    "Tutta la Svizzera": {
        "adzuna":    "",
        "jobs_rss":  "",
        "jobup_rss": "",
        "label":     "CH",
    },
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


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "fr-CH,fr;q=0.9,en;q=0.8",
}


def _get(url: str, params: dict | None = None, timeout: int = 12) -> Optional[requests.Response]:
    try:
        r = requests.get(url, params=params, headers=_HEADERS, timeout=timeout)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        logger.warning("HTTP error %s -> %s", url, e)
        return None


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return unescape(text).strip()


def _parse_rss_items(content: bytes, source: str, max_results: int) -> List[Job]:
    jobs: List[Job] = []
    try:
        root    = ET.fromstring(content)
        channel = root.find("channel")
        if channel is None:
            return jobs
        for item in channel.findall("item")[:max_results]:
            title       = _strip_html(item.findtext("title", "—"))
            link        = item.findtext("link", "")
            pub_date    = item.findtext("pubDate", "")[:16]
            description = _strip_html(item.findtext("description", ""))
            company, location = "—", "—"
            lines = [l.strip() for l in description.split("\n") if l.strip()]
            if len(lines) >= 2:
                company, location = lines[0], lines[1]
            elif len(lines) == 1:
                company = lines[0]
            jobs.append(Job(
                title=title, company=company, location=location,
                url=link, source=source, posted_date=pub_date,
                description=description,
            ))
    except ET.ParseError as e:
        logger.warning("%s RSS parse error: %s", source, e)
    return jobs


def _search_jobsch_rss(query: str, region_code: str, max_results: int) -> List[Job]:
    params: dict = {"term": query, "rss": "1"}
    if region_code:
        params["region"] = region_code
    r = _get("https://www.jobs.ch/fr/offres-d-emploi/", params=params)
    if r is None:
        return []
    jobs = _parse_rss_items(r.content, "jobs.ch", max_results)
    logger.info("jobs.ch RSS: %d risultati", len(jobs))
    return jobs


def _search_jobup_rss(query: str, region_code: str, max_results: int) -> List[Job]:
    params: dict = {"term": query, "rss": "1"}
    if region_code:
        params["region"] = region_code
    r = _get("https://www.jobup.ch/fr/emplois/", params=params)
    if r is None:
        return []
    jobs = _parse_rss_items(r.content, "jobup.ch", max_results)
    logger.info("jobup.ch RSS: %d risultati", len(jobs))
    return jobs


def _search_adzuna(query: str, region_label: str, max_results: int,
                   app_id: str, app_key: str) -> List[Job]:
    jobs: List[Job] = []
    params: dict = {
        "app_id":           app_id,
        "app_key":          app_key,
        "what":             query,
        "results_per_page": min(max_results, 50),
        "content-type":     "application/json",
    }
    if region_label:
        params["where"] = region_label
    r = _get("https://api.adzuna.com/v1/api/jobs/ch/search/1", params=params)
    if r is None:
        return jobs
    try:
        data = r.json()
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
            ))
    except Exception as e:
        logger.warning("Adzuna parse error: %s", e)
    logger.info("Adzuna: %d risultati", len(jobs))
    return jobs


def search_jobs(
    query: str,
    region_name: str,
    max_results: int = 20,
    sources: List[str] | None = None,
    adzuna_app_id: str = "",
    adzuna_app_key: str = "",
) -> List[Job]:
    if sources is None:
        sources = ["jobs.ch", "jobup.ch", "adzuna"]

    region_info = REGIONS.get(region_name, REGIONS["Svizzera Romanda"])
    all_jobs:  List[Job] = []
    seen_urls: set[str]  = set()
    per_source = max(max_results // max(len(sources), 1), 10)

    def _add(new_jobs: List[Job]) -> None:
        for j in new_jobs:
            if j.url and j.url not in seen_urls:
                seen_urls.add(j.url)
                all_jobs.append(j)

    if "jobs.ch" in sources:
        try:
            _add(_search_jobsch_rss(query, region_info["jobs_rss"], per_source))
        except Exception as e:
            logger.error("jobs.ch RSS failed: %s", e)

    if "jobup.ch" in sources:
        time.sleep(0.5)
        try:
            _add(_search_jobup_rss(query, region_info["jobup_rss"], per_source))
        except Exception as e:
            logger.error("jobup.ch RSS failed: %s", e)

    if "adzuna" in sources and adzuna_app_id and adzuna_app_key:
        time.sleep(0.5)
        try:
            _add(_search_adzuna(query, region_info["adzuna"], per_source,
                                adzuna_app_id, adzuna_app_key))
        except Exception as e:
            logger.error("Adzuna failed: %s", e)

    return all_jobs[:max_results]


def get_job_detail(url: str) -> str:
    from bs4 import BeautifulSoup
    r = _get(url)
    if r is None:
        return ""
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    for selector in ["[class*='description']", "[class*='job-detail']", "article", "main"]:
        el = soup.select_one(selector)
        if el:
            return el.get_text(separator="\n", strip=True)[:3000]
    return soup.get_text(separator="\n", strip=True)[:2000]
