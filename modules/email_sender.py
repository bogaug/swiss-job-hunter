"""
email_sender.py – Invio candidature via SMTP (Gmail, Outlook, ecc.)
Supporta allegati PDF (CV) e testo HTML.
"""

import smtplib
import ssl
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Tuple
import io

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Config test
# ──────────────────────────────────────────────────────────────────────────────
def test_email_config(
    host: str, port: int, user: str, password: str
) -> bool:
    """Verifica la connessione SMTP senza inviare email."""
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=8) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(user, password)
        return True
    except Exception as e:
        logger.warning("SMTP test fallito: %s", e)
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Formattazione HTML
# ──────────────────────────────────────────────────────────────────────────────
def _text_to_html(text: str) -> str:
    """Converte testo plain in HTML semplice con paragrafi."""
    paragraphs = text.split("\n\n")
    html_parts = ["<html><body style='font-family:Arial,sans-serif;font-size:14px;line-height:1.6;color:#333;'>"]
    for p in paragraphs:
        p_clean = p.strip().replace("\n", "<br>")
        if p_clean:
            html_parts.append(f"<p>{p_clean}</p>")
    html_parts.append("</body></html>")
    return "\n".join(html_parts)


# ──────────────────────────────────────────────────────────────────────────────
# Invio email
# ──────────────────────────────────────────────────────────────────────────────
def send_email(
    smtp_config: dict,
    to_email: str,
    subject: str,
    body: str,
    cv_file=None,             # file-like object o None
    cv_filename: str = "CV.pdf",
    extra_attachments: Optional[list] = None,
) -> Tuple[bool, str]:
    """
    Invia un'email di candidatura con allegati opzionali.

    Args:
        smtp_config:       Dict con host, port, user, password, sender_name, sender_email
        to_email:          Indirizzo destinatario
        subject:           Oggetto email
        body:              Corpo email (testo plain)
        cv_file:           File-like object del CV (pdf), o None
        cv_filename:       Nome file allegato CV
        extra_attachments: Lista di (file_like, filename) aggiuntivi

    Returns:
        (success: bool, message: str)
    """
    host     = smtp_config.get("host", "smtp.gmail.com")
    port     = int(smtp_config.get("port", 587))
    user     = smtp_config.get("user", "")
    password = smtp_config.get("password", "")
    sender   = smtp_config.get("sender_email", user)
    name     = smtp_config.get("sender_name", "")

    if not user or not password:
        return False, "Credenziali SMTP mancanti. Configurale nella sidebar."

    # ── Costruzione email ──────────────────────────────────────────────────
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{name} <{sender}>" if name else sender
    msg["To"]      = to_email
    msg["X-Mailer"] = "Swiss Job Hunter"

    # Corpo plain + HTML
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(_text_to_html(body), "html", "utf-8"))

    # Allegato CV
    if cv_file is not None:
        try:
            if hasattr(cv_file, "read"):
                cv_data = cv_file.read()
            else:
                cv_data = cv_file

            part = MIMEBase("application", "octet-stream")
            part.set_payload(cv_data)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{cv_filename}"',
            )
            msg.attach(part)
        except Exception as e:
            logger.warning("Allegato CV non aggiunto: %s", e)

    # Allegati extra
    if extra_attachments:
        for (f_obj, f_name) in extra_attachments:
            try:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f_obj.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f'attachment; filename="{f_name}"')
                msg.attach(part)
            except Exception as e:
                logger.warning("Allegato %s non aggiunto: %s", f_name, e)

    # ── Invio SMTP ─────────────────────────────────────────────────────────
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(user, password)
            server.sendmail(sender, [to_email], msg.as_string())

        logger.info("Email inviata a %s: %s", to_email, subject)
        return True, f"Email inviata con successo a {to_email}"

    except smtplib.SMTPAuthenticationError:
        msg_err = (
            "Autenticazione SMTP fallita. Per Gmail usa una 'App Password' "
            "(non la password del tuo account): "
            "https://myaccount.google.com/apppasswords"
        )
        logger.error(msg_err)
        return False, msg_err
    except smtplib.SMTPRecipientsRefused:
        return False, f"Destinatario rifiutato: {to_email}"
    except smtplib.SMTPException as e:
        logger.error("SMTP error: %s", e)
        return False, str(e)
    except Exception as e:
        logger.error("Errore generico invio email: %s", e)
        return False, str(e)


# ──────────────────────────────────────────────────────────────────────────────
# Preview email (per test senza invio)
# ──────────────────────────────────────────────────────────────────────────────
def preview_email(
    to_email: str,
    subject: str,
    body: str,
    sender_name: str = "",
) -> str:
    """Restituisce una preview testuale dell'email."""
    lines = [
        f"Da:       {sender_name}",
        f"A:        {to_email}",
        f"Oggetto:  {subject}",
        "─" * 50,
        body,
    ]
    return "\n".join(lines)
