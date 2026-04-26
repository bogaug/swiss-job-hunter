"""
tracker.py – Tracciamento candidature su SQLite.
Schema minimo, facile da esportare in CSV/Excel.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "applications.db"

STATUS_OPTIONS = [
    "Inviata",
    "In revisione",
    "Colloquio telefonico",
    "Colloquio in presenza",
    "Assessment",
    "Offerta ricevuta",
    "Accettata",
    "Rifiutata",
    "Ritirata",
]

# ──────────────────────────────────────────────────────────────────────────────
# Init DB
# ──────────────────────────────────────────────────────────────────────────────
def init_db() -> None:
    """Crea il database e le tabelle se non esistono."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title       TEXT NOT NULL,
            company         TEXT NOT NULL,
            location        TEXT,
            url             TEXT,
            hr_email        TEXT,
            status          TEXT DEFAULT 'Inviata',
            cover_letter    TEXT,
            sent_date       TEXT,
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now')),
            tags            TEXT DEFAULT '[]'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS status_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id  INTEGER NOT NULL,
            old_status      TEXT,
            new_status      TEXT,
            note            TEXT,
            changed_at      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(application_id) REFERENCES applications(id)
        )
    """)

    conn.commit()
    conn.close()
    logger.debug("DB inizializzato: %s", DB_PATH)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ──────────────────────────────────────────────────────────────────────────────
# CRUD
# ──────────────────────────────────────────────────────────────────────────────
def add_application(
    job_title: str,
    company: str,
    location: str = "",
    url: str = "",
    hr_email: str = "",
    cover_letter: str = "",
    status: str = "Inviata",
    notes: str = "",
    tags: Optional[List[str]] = None,
) -> int:
    """Aggiunge una nuova candidatura. Restituisce l'ID creato."""
    conn = _conn()
    cur  = conn.cursor()
    now  = datetime.now().isoformat(timespec="seconds")

    cur.execute("""
        INSERT INTO applications
            (job_title, company, location, url, hr_email, cover_letter,
             status, notes, sent_date, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_title, company, location, url, hr_email, cover_letter,
        status, notes, now, json.dumps(tags or [])
    ))

    app_id = cur.lastrowid
    # Storia
    cur.execute("""
        INSERT INTO status_history (application_id, old_status, new_status, note)
        VALUES (?, ?, ?, ?)
    """, (app_id, None, status, "Candidatura creata"))

    conn.commit()
    conn.close()
    return app_id


def get_applications(status_filter: Optional[List[str]] = None) -> List[dict]:
    """Restituisce tutte le candidature (opzionalmente filtrate per stato)."""
    conn = _conn()
    cur  = conn.cursor()

    if status_filter:
        placeholders = ",".join("?" * len(status_filter))
        cur.execute(
            f"SELECT * FROM applications WHERE status IN ({placeholders}) ORDER BY sent_date DESC",
            status_filter
        )
    else:
        cur.execute("SELECT * FROM applications ORDER BY sent_date DESC")

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_application(app_id: int) -> Optional[dict]:
    """Restituisce una candidatura per ID."""
    conn = _conn()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_application_status(
    app_id: int,
    new_status: str,
    notes: str = "",
) -> None:
    """Aggiorna lo stato di una candidatura."""
    conn = _conn()
    cur  = conn.cursor()

    # Stato attuale per la history
    cur.execute("SELECT status FROM applications WHERE id = ?", (app_id,))
    row = cur.fetchone()
    old_status = row["status"] if row else None

    cur.execute("""
        UPDATE applications
        SET status = ?, notes = CASE WHEN ? != '' THEN ? ELSE notes END,
            updated_at = datetime('now')
        WHERE id = ?
    """, (new_status, notes, notes, app_id))

    cur.execute("""
        INSERT INTO status_history (application_id, old_status, new_status, note)
        VALUES (?, ?, ?, ?)
    """, (app_id, old_status, new_status, notes))

    conn.commit()
    conn.close()


def delete_application(app_id: int) -> None:
    """Elimina una candidatura e la sua storia."""
    conn = _conn()
    cur  = conn.cursor()
    cur.execute("DELETE FROM status_history WHERE application_id = ?", (app_id,))
    cur.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()


def get_status_history(app_id: int) -> List[dict]:
    """Restituisce la cronologia degli stati di una candidatura."""
    conn = _conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT * FROM status_history
        WHERE application_id = ?
        ORDER BY changed_at ASC
    """, (app_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ──────────────────────────────────────────────────────────────────────────────
# Stats
# ──────────────────────────────────────────────────────────────────────────────
def get_stats() -> dict:
    """Restituisce statistiche aggregate delle candidature."""
    conn = _conn()
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM applications")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT status, COUNT(*) as n
        FROM applications
        GROUP BY status
    """)
    by_status = {row["status"]: row["n"] for row in cur.fetchall()}

    cur.execute("""
        SELECT company, COUNT(*) as n
        FROM applications
        GROUP BY company
        ORDER BY n DESC
        LIMIT 5
    """)
    top_companies = [(r["company"], r["n"]) for r in cur.fetchall()]

    conn.close()

    interviews = sum(
        by_status.get(s, 0)
        for s in ["Colloquio telefonico", "Colloquio in presenza", "Assessment"]
    )

    return {
        "total":         total,
        "pending":       by_status.get("Inviata", 0) + by_status.get("In revisione", 0),
        "interviews":    interviews,
        "offers":        by_status.get("Offerta ricevuta", 0) + by_status.get("Accettata", 0),
        "rejected":      by_status.get("Rifiutata", 0),
        "by_status":     by_status,
        "top_companies": top_companies,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Export
# ──────────────────────────────────────────────────────────────────────────────
def export_to_csv() -> str:
    """Esporta le candidature in formato CSV (stringa)."""
    import csv
    import io

    apps = get_applications()
    if not apps:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "job_title", "company", "location", "status",
                    "sent_date", "hr_email", "url", "notes"],
        extrasaction="ignore"
    )
    writer.writeheader()
    writer.writerows(apps)
    return output.getvalue()
