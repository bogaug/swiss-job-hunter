"""
ai_generator.py – Generazione lettera di motivazione con Claude (Anthropic API).
"""

import anthropic
import logging
from typing import Optional

logger = logging.getLogger(__name__)

LANG_PROMPTS = {
    "Francese": {
        "lang": "français",
        "greeting": "Madame, Monsieur",
        "closing": "Dans l'attente de votre réponse, je vous adresse mes meilleures salutations.",
    },
    "Italiano": {
        "lang": "italiano",
        "greeting": "Gentile Responsabile delle Risorse Umane",
        "closing": "In attesa di una risposta, porgo distinti saluti.",
    },
    "Inglese": {
        "lang": "English",
        "greeting": "Dear Hiring Manager",
        "closing": "I look forward to hearing from you. Kind regards,",
    },
    "Tedesco": {
        "lang": "Deutsch",
        "greeting": "Sehr geehrte Damen und Herren",
        "closing": "Mit freundlichen Grüssen,",
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Prompt builder
# ──────────────────────────────────────────────────────────────────────────────
def _build_system_prompt(language: str) -> str:
    lang_info = LANG_PROMPTS.get(language, LANG_PROMPTS["Francese"])
    lang = lang_info["lang"]
    return f"""Tu sei un esperto consulente di carriera svizzero, specializzato nella redazione di lettere di motivazione in {lang} per il mercato del lavoro svizzero.

Le tue lettere di motivazione devono:
- Essere scritte ESCLUSIVAMENTE in {lang}
- Seguire le convenzioni epistolari svizzere (professionale, preciso, non eccessivamente formale)
- Evidenziare i match concreti tra il profilo del candidato e i requisiti dell'offerta
- Avere una struttura chiara: apertura / valore aggiunto del candidato / interesse per l'azienda / chiusura
- Durare 3-4 paragrafi (circa 250-350 parole)
- NON includere informazioni inventate — usa solo ciò che ti viene fornito
- NON aggiungere header, date, indirizzi — solo il corpo della lettera
"""


def _build_user_prompt(
    job_title: str,
    company: str,
    location: str,
    job_description: str,
    candidate: dict,
    extra_notes: str,
    language: str,
) -> str:
    lang_info = LANG_PROMPTS.get(language, LANG_PROMPTS["Francese"])

    desc_block = f"\n\nDescrizione dell'offerta:\n{job_description[:2000]}" if job_description.strip() else ""

    return f"""Scrivi una lettera di motivazione per la seguente offerta di lavoro:{desc_block}

━━━━━━━━━━━━━━━━━━━━━━━━
DATI OFFERTA
Posizione: {job_title}
Azienda: {company}
Luogo: {location}
━━━━━━━━━━━━━━━━━━━━━━━━
PROFILO CANDIDATO
Nome: {candidate.get('name', '')}
Ruolo target: {candidate.get('role', '')}
Competenze tecniche: {candidate.get('skills', '')}
Lingue: {candidate.get('languages', 'Italiano (madrelingua), Francese C1, Inglese C1')}
Formazione: {candidate.get('education', '')}
Esperienza: {candidate.get('experience', '')}
━━━━━━━━━━━━━━━━━━━━━━━━
{f'NOTE SPECIFICHE DEL CANDIDATO: {extra_notes}' if extra_notes.strip() else ''}

Inizia direttamente con "{lang_info["greeting"]}," senza preamboli.
Termina con "{lang_info["closing"]}"
Poi lascia una riga vuota e scrivi solo il nome: {candidate.get('name', '')}
"""


# ──────────────────────────────────────────────────────────────────────────────
# Generator
# ──────────────────────────────────────────────────────────────────────────────
def generate_cover_letter(
    api_key: str,
    job_title: str,
    company: str,
    location: str,
    job_description: str,
    candidate: dict,
    extra_notes: str = "",
    language: str = "Francese",
    model: str = "claude-opus-4-5",
    max_tokens: int = 1200,
) -> str:
    """
    Genera una lettera di motivazione con Claude.

    Args:
        api_key:         Anthropic API key
        job_title:       Titolo posizione
        company:         Nome azienda
        location:        Luogo offerta
        job_description: Testo descrizione offerta (opzionale ma migliora qualità)
        candidate:       Dict con nome, skills, lingue, esperienza, ecc.
        extra_notes:     Istruzioni extra per l'AI
        language:        "Francese" | "Italiano" | "Inglese" | "Tedesco"
        model:           Modello Claude da usare
        max_tokens:      Token massimi risposta

    Returns:
        Testo della lettera di motivazione.
    """
    client = anthropic.Anthropic(api_key=api_key)

    system = _build_system_prompt(language)
    user   = _build_user_prompt(
        job_title, company, location, job_description,
        candidate, extra_notes, language
    )

    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text.strip()
    except anthropic.APIError as e:
        logger.error("Anthropic API error: %s", e)
        raise RuntimeError(f"Errore API Anthropic: {e}") from e


# ──────────────────────────────────────────────────────────────────────────────
# Personalizzazione oggetto email
# ──────────────────────────────────────────────────────────────────────────────
def generate_email_subject(
    api_key: str,
    job_title: str,
    company: str,
    candidate_name: str,
    language: str = "Francese",
) -> str:
    """Genera un oggetto email professionale per la candidatura."""
    client = anthropic.Anthropic(api_key=api_key)

    lang = LANG_PROMPTS.get(language, LANG_PROMPTS["Francese"])["lang"]
    prompt = (
        f"Genera un oggetto email professionale in {lang} per una candidatura spontanea / "
        f"risposta a un'offerta. Posizione: '{job_title}' presso '{company}'. "
        f"Candidato: {candidate_name}. Rispondi solo con il testo dell'oggetto, nient'altro."
    )

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        # Fallback generico
        subjects = {
            "Francese": f"Candidature – {job_title} | {candidate_name}",
            "Italiano": f"Candidatura – {job_title} | {candidate_name}",
            "Inglese":  f"Application – {job_title} | {candidate_name}",
            "Tedesco":  f"Bewerbung – {job_title} | {candidate_name}",
        }
        return subjects.get(language, f"Candidatura – {job_title} | {candidate_name}")
