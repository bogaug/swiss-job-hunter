"""
app.py – Swiss Job Hunter
Streamlit app per cercare offerte, generare lettere con AI e tracciare candidature.

Avvio: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.WARNING)

from modules import (
    search_jobs, get_job_detail, REGIONS, Job,
    generate_cover_letter, generate_email_subject,
    send_email, test_email_config, preview_email,
    init_db, add_application, get_applications, get_application,
    update_application_status, delete_application,
    get_stats, get_status_history, export_to_csv,
    STATUS_OPTIONS,
)

# ──────────────────────────────────────────────────────────────────────────────
# Page config & CSS
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Swiss Job Hunter 🇨🇭",
    page_icon="🇨🇭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Palette ── */
:root {
    --red:   #DC143C;
    --red2:  #B01030;
    --bg:    #F8F9FA;
    --card:  #FFFFFF;
    --border:#E0E4EA;
    --muted: #6C757D;
    --green: #2ECC71;
    --amber: #F39C12;
    --blue:  #3498DB;
}

/* ── Header ── */
.sjh-header {
    background: linear-gradient(135deg, var(--red) 0%, var(--red2) 100%);
    border-radius: 12px;
    padding: 1.4rem 2rem;
    color: white;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.sjh-header h1 { margin: 0; font-size: 1.7rem; }
.sjh-header p  { margin: 0; opacity: .85; font-size: .95rem; }

/* ── Job card ── */
.job-card {
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: .8rem;
    background: var(--card);
    transition: box-shadow .15s;
}
.job-card:hover { box-shadow: 0 4px 18px rgba(0,0,0,.07); }
.job-card .title { font-size: 1.05rem; font-weight: 600; color: #111; margin-bottom: .2rem; }
.job-card .meta  { color: var(--muted); font-size: .87rem; }

/* ── KPI cards ── */
.kpi {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    text-align: center;
}
.kpi .number { font-size: 2rem; font-weight: 700; color: var(--red); }
.kpi .label  { color: var(--muted); font-size: .85rem; margin-top: .2rem; }

/* ── Status badge ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: .78rem;
    font-weight: 600;
}
.badge-sent       { background:#EBF5FB; color: var(--blue); }
.badge-interview  { background:#FEF9E7; color: var(--amber); }
.badge-offer      { background:#EAFAF1; color: var(--green); }
.badge-rejected   { background:#FDEDEC; color: #E74C3C; }
.badge-default    { background:#F2F3F4; color: var(--muted); }

/* ── Misc ── */
.section-title { font-size: 1.2rem; font-weight: 600; margin: 1rem 0 .5rem; }
.hint { color: var(--muted); font-size: .83rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Init
# ──────────────────────────────────────────────────────────────────────────────
init_db()

# Session state defaults
defaults = {
    "search_results":  [],
    "selected_job":    None,
    "generated_letter":"",
    "form_data":       {},
    "search_done":     False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar – configurazione
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🇨🇭 Swiss Job Hunter")
    st.markdown("---")

    page = st.radio(
        "Pagina",
        ["🔍 Cerca Offerte", "✍️ Nuova Candidatura", "📊 Dashboard"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### ⚙️ Configurazione")

    # ── Profilo candidato ────────────────────────────────────────────────
    with st.expander("👤 Profilo Candidato", expanded=False):
        c_name   = st.text_input("Nome Completo",   value=os.getenv("CANDIDATE_NAME", ""))
        c_email  = st.text_input("La tua Email",    value=os.getenv("CANDIDATE_EMAIL", ""))
        c_role   = st.text_input("Ruolo ricercato", value=os.getenv("CANDIDATE_ROLE", "Data Engineer"))
        c_skills = st.text_area(
            "Competenze principali",
            value=os.getenv("CANDIDATE_SKILLS",
                "Python, SQL, ETL, Apache Spark, Power BI, Machine Learning, "
                "Docker, Azure, BigQuery, Kafka"),
            height=100,
        )
        c_edu  = st.text_input("Formazione", value=os.getenv("CANDIDATE_EDUCATION",
            "BSc Data Engineering, HEIA-FR / HES-SO (2025)"))
        c_exp  = st.text_area("Esperienze rilevanti",
            value=os.getenv("CANDIDATE_EXPERIENCE",
                "Assistant Data Analyst, Cornèr Banque SA – pipeline ETL, Power BI, SQL"),
            height=80)
        c_langs = st.text_input("Lingue",
            value=os.getenv("CANDIDATE_LANGUAGES",
                "Italiano (madrelingua), Francese C1, Inglese C1, Spagnolo C1, Tedesco A2"))
        c_letter_lang = st.selectbox(
            "Lingua lettera motivazione",
            ["Francese", "Italiano", "Inglese", "Tedesco"],
            index=0,
        )

    candidate = {
        "name":      c_name,
        "email":     c_email,
        "role":      c_role,
        "skills":    c_skills,
        "education": c_edu,
        "experience":c_exp,
        "languages": c_langs,
        "language":  c_letter_lang,
    }

    # ── API Key ──────────────────────────────────────────────────────────
    with st.expander("🤖 Anthropic API", expanded=False):
        api_key = st.text_input(
            "API Key",
            type="password",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            help="Ottieni la tua key su console.anthropic.com",
        )
        if api_key:
            st.success("✅ API Key configurata")
        else:
            st.info("Inserisci la tua Anthropic API Key per generare lettere con AI")

    # ── SMTP ─────────────────────────────────────────────────────────────
    with st.expander("📧 Email SMTP", expanded=False):
        smtp_host = st.text_input("SMTP Host", value=os.getenv("SMTP_HOST", "smtp.gmail.com"))
        smtp_port = st.number_input("Porta",    value=int(os.getenv("SMTP_PORT", 587)), step=1)
        smtp_user = st.text_input("Mittente",   value=os.getenv("SMTP_USER", ""))
        smtp_pass = st.text_input("App Password", type="password",
                                   value=os.getenv("SMTP_PASSWORD", ""),
                                   help="Gmail: usa App Password, non la password principale")
        if st.button("🔌 Testa SMTP"):
            if smtp_user and smtp_pass:
                with st.spinner("Test connessione..."):
                    ok = test_email_config(smtp_host, smtp_port, smtp_user, smtp_pass)
                st.success("✅ Connessione OK!") if ok else st.error("❌ Connessione fallita")
            else:
                st.warning("Inserisci user e password")

smtp_config = {
    "host":         smtp_host,
    "port":         int(smtp_port),
    "user":         smtp_user,
    "password":     smtp_pass,
    "sender_name":  c_name,
    "sender_email": smtp_user,
}


# ──────────────────────────────────────────────────────────────────────────────
# Helper badge
# ──────────────────────────────────────────────────────────────────────────────
def status_badge(status: str) -> str:
    cls_map = {
        "Inviata":               "badge-sent",
        "In revisione":          "badge-sent",
        "Colloquio telefonico":  "badge-interview",
        "Colloquio in presenza": "badge-interview",
        "Assessment":            "badge-interview",
        "Offerta ricevuta":      "badge-offer",
        "Accettata":             "badge-offer",
        "Rifiutata":             "badge-rejected",
        "Ritirata":              "badge-rejected",
    }
    cls = cls_map.get(status, "badge-default")
    return f'<span class="badge {cls}">{status}</span>'


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CERCA OFFERTE
# ══════════════════════════════════════════════════════════════════════════════
if page == "🔍 Cerca Offerte":
    st.markdown("""
    <div class="sjh-header">
        <div>
            <h1>🔍 Cerca Offerte di Lavoro</h1>
            <p>Ricerca su jobs.ch e jobup.ch per regione svizzera</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Barra di ricerca ──────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
    with col1:
        query = st.text_input("🔎 Parola chiave", placeholder="Data Engineer, Python, Analytics…")
    with col2:
        region = st.selectbox(
            "📍 Regione",
            list(REGIONS.keys()),
            format_func=lambda r: f"{r} ({REGIONS[r]['label']})",
        )
    with col3:
        max_results = st.number_input("Max risultati", 5, 50, 20, step=5)
    with col4:
        sources = st.multiselect(
            "Fonti",
            ["jobup", "jobs.ch"],
            default=["jobup", "jobs.ch"],
            label_visibility="visible",
        )

    col_btn, col_info = st.columns([1, 5])
    with col_btn:
        search_btn = st.button("🔍 Cerca", type="primary", use_container_width=True)

    if search_btn:
        if not query.strip():
            st.warning("⚠️ Inserisci una parola chiave")
        elif not sources:
            st.warning("⚠️ Seleziona almeno una fonte")
        else:
            with st.spinner(f"Ricerca '{query}' in {region}…"):
                try:
                    jobs = search_jobs(query, region, max_results, sources)
                    st.session_state.search_results = jobs
                    st.session_state.search_done = True
                except Exception as e:
                    st.error(f"Errore durante la ricerca: {e}")
                    st.session_state.search_results = []

    # ── Risultati ─────────────────────────────────────────────────────────
    if st.session_state.search_done:
        jobs = st.session_state.search_results
        if jobs:
            st.success(f"✅ {len(jobs)} offerte trovate")

            # Filtro rapido
            col_f1, col_f2 = st.columns([3, 2])
            with col_f1:
                filter_text = st.text_input("🔎 Filtra risultati", placeholder="filtra per azienda, titolo…")
            with col_f2:
                source_filter = st.multiselect("Fonte", ["jobup.ch", "jobs.ch"], default=[])

            filtered = jobs
            if filter_text:
                q = filter_text.lower()
                filtered = [j for j in filtered if q in j.title.lower() or q in j.company.lower()]
            if source_filter:
                filtered = [j for j in filtered if j.source in source_filter]

            st.markdown(f"<span class='hint'>Mostrando {len(filtered)} su {len(jobs)} risultati</span>",
                        unsafe_allow_html=True)

            for i, job in enumerate(filtered):
                src_tag = f"<span style='background:#EBF5FB;color:#3498DB;padding:1px 7px;border-radius:10px;font-size:.8rem'>{job.source}</span>"
                btn_col, info_col = st.columns([1, 8])

                with info_col:
                    st.markdown(f"""
                    <div class="job-card">
                        <div class="title">{job.title}</div>
                        <div class="meta">
                            🏢 <b>{job.company}</b> &nbsp;|&nbsp;
                            📍 {job.location} &nbsp;|&nbsp;
                            {src_tag}
                            {"&nbsp;|&nbsp; 📅 " + job.posted_date if job.posted_date else ""}
                        </div>
                        <div style="margin-top:.4rem">
                            <a href="{job.url}" target="_blank" style="font-size:.85rem;color:#3498DB">
                                🔗 Vedi offerta completa
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with btn_col:
                    st.markdown("<div style='margin-top:1rem'>", unsafe_allow_html=True)
                    if st.button("✍️", key=f"sel_{i}", help="Seleziona per candidatura"):
                        st.session_state.selected_job = job
                        st.session_state.generated_letter = ""
                        st.session_state.form_data = {
                            "job_title": job.title,
                            "company":   job.company,
                            "location":  job.location,
                            "job_url":   job.url,
                            "hr_email":  "",
                            "job_description": "",
                        }
                        st.toast(f"✅ '{job.title}' selezionato — vai su ✍️ Nuova Candidatura")
                    st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.warning("Nessun risultato. Prova parole chiave diverse o seleziona 'Tutta la Svizzera'.")
            st.info("💡 **Suggerimento:** i siti di lavoro svizzeri possono bloccare le richieste automatiche. "
                    "Se la ricerca è vuota, prova a incollare manualmente il testo dell'offerta nella tab '✍️ Nuova Candidatura'.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: NUOVA CANDIDATURA
# ══════════════════════════════════════════════════════════════════════════════
elif page == "✍️ Nuova Candidatura":
    st.markdown("""
    <div class="sjh-header">
        <div>
            <h1>✍️ Nuova Candidatura</h1>
            <p>Genera la tua lettera con AI e inviala direttamente</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Avviso se job selezionato
    if st.session_state.selected_job:
        j = st.session_state.selected_job
        st.info(f"**Offerta selezionata:** {j.title} @ {j.company} | {j.location}  "
                f"— [Vedi su {j.source}]({j.url})")

    tab1, tab2, tab3 = st.tabs(["📋 1. Dettagli Offerta", "🤖 2. Genera Lettera", "📧 3. Invia Email"])

    # ── Tab 1: Dettagli ────────────────────────────────────────────────────
    with tab1:
        st.markdown("<div class='section-title'>Dettagli Offerta di Lavoro</div>", unsafe_allow_html=True)

        fd = st.session_state.form_data

        col1, col2 = st.columns(2)
        with col1:
            job_title = st.text_input("Titolo posizione *", value=fd.get("job_title", ""))
            company   = st.text_input("Azienda *",          value=fd.get("company", ""))
            location  = st.text_input("Luogo",              value=fd.get("location", ""))
        with col2:
            job_url   = st.text_input("URL offerta",         value=fd.get("job_url", ""))
            hr_email  = st.text_input("📧 Email HR / Contatto *", value=fd.get("hr_email", ""),
                                      placeholder="hr@azienda.ch")

        job_description = st.text_area(
            "📄 Descrizione offerta  "
            "<span class='hint'>(incolla qui il testo dell'offerta — migliora notevolmente la qualità della lettera)</span>",
            value=fd.get("job_description", ""),
            height=220,
        )

        # Auto-fetch description
        if job_url and st.button("⬇️ Carica descrizione dall'URL"):
            with st.spinner("Download pagina offerta…"):
                try:
                    desc = get_job_detail(job_url)
                    if desc:
                        job_description = desc
                        st.success(f"✅ Descrizione caricata ({len(desc)} caratteri)")
                    else:
                        st.warning("Non è stato possibile estrarre la descrizione. Incollala manualmente.")
                except Exception as e:
                    st.error(f"Errore: {e}")

        if st.button("💾 Salva dettagli", type="primary"):
            st.session_state.form_data = {
                "job_title":        job_title,
                "company":          company,
                "location":         location,
                "job_url":          job_url,
                "hr_email":         hr_email,
                "job_description":  job_description,
            }
            st.success("✅ Dettagli salvati — vai al tab '🤖 2. Genera Lettera'")

    # ── Tab 2: Genera Lettera ──────────────────────────────────────────────
    with tab2:
        st.markdown("<div class='section-title'>🤖 Generazione con Claude AI</div>", unsafe_allow_html=True)

        fd = st.session_state.form_data

        # Riepilogo
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Posizione:** {fd.get('job_title', '—')}")
            st.markdown(f"**Azienda:** {fd.get('company', '—')}")
        with col2:
            st.markdown(f"**Lingua lettera:** {candidate['language']}")
            st.markdown(f"**Candidato:** {candidate['name'] or '—'}")

        if not fd.get("job_title"):
            st.warning("⚠️ Completa prima i dettagli nel tab '📋 1. Dettagli Offerta'")

        extra_notes = st.text_area(
            "📝 Istruzioni aggiuntive per l'AI",
            placeholder="es: enfatizza l'esperienza bancaria, menziona il progetto X, "
                        "tono leggermente più informale…",
            height=80,
        )

        col_btn, col_model = st.columns([2, 2])
        with col_model:
            model = st.selectbox(
                "Modello Claude",
                ["claude-opus-4-5", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
                help="Opus = qualità massima | Haiku = veloce ed economico",
            )

        with col_btn:
            gen_btn = st.button("🤖 Genera Lettera", type="primary", use_container_width=True)

        if gen_btn:
            if not api_key:
                st.error("❌ Inserisci la tua Anthropic API Key nella sidebar")
            elif not fd.get("job_title"):
                st.error("❌ Salva prima i dettagli dell'offerta nel tab precedente")
            elif not candidate.get("name"):
                st.error("❌ Inserisci il tuo nome nella sidebar")
            else:
                with st.spinner("Claude sta scrivendo la tua lettera…"):
                    try:
                        letter = generate_cover_letter(
                            api_key=api_key,
                            job_title=fd.get("job_title", ""),
                            company=fd.get("company", ""),
                            location=fd.get("location", ""),
                            job_description=fd.get("job_description", ""),
                            candidate=candidate,
                            extra_notes=extra_notes,
                            language=candidate["language"],
                            model=model,
                        )
                        st.session_state.generated_letter = letter
                        st.success("✅ Lettera generata!")
                    except Exception as e:
                        st.error(f"Errore generazione: {e}")

        if st.session_state.generated_letter:
            st.markdown("### 📄 Lettera di Motivazione")
            edited = st.text_area(
                "Modifica la lettera se necessario:",
                value=st.session_state.generated_letter,
                height=450,
                key="letter_editor",
            )
            st.session_state.generated_letter = edited

            col_dl1, col_dl2, col_regen = st.columns(3)
            with col_dl1:
                fname = f"lettera_{fd.get('company','candidatura').replace(' ','_')}.txt"
                st.download_button(
                    "⬇️ Scarica .txt",
                    data=edited,
                    file_name=fname,
                    mime="text/plain",
                )
            with col_regen:
                if st.button("🔄 Rigenera"):
                    st.session_state.generated_letter = ""
                    st.rerun()

    # ── Tab 3: Invia Email ─────────────────────────────────────────────────
    with tab3:
        st.markdown("<div class='section-title'>📧 Invia Candidatura via Email</div>", unsafe_allow_html=True)

        fd = st.session_state.form_data

        col1, col2 = st.columns(2)
        with col1:
            to_email = st.text_input("📧 Destinatario (HR)", value=fd.get("hr_email", ""))

            # Suggerisci oggetto
            default_subject = f"Candidatura – {fd.get('job_title','')} | {candidate.get('name','')}"
            email_subject = st.text_input("Oggetto email", value=default_subject)

            if api_key and fd.get("job_title") and st.button("✨ Genera oggetto con AI"):
                with st.spinner():
                    try:
                        subj = generate_email_subject(
                            api_key, fd.get("job_title",""),
                            fd.get("company",""), candidate.get("name",""),
                            candidate["language"],
                        )
                        email_subject = subj
                        st.success(f"Oggetto: {subj}")
                    except Exception:
                        pass

        with col2:
            cv_file = st.file_uploader("📎 Allega CV (PDF)", type=["pdf"])
            cv_name = st.text_input("Nome file CV allegato", value=f"CV_{candidate.get('name','').replace(' ','_')}.pdf")

        include_letter = st.checkbox(
            "📄 Includi lettera nel corpo email",
            value=True,
            help="Se disabilitato, allega la lettera come file .txt"
        )

        email_intro = st.text_area(
            "Testo introduttivo email",
            value=(
                f"Gentile Responsabile delle Risorse Umane,\n\n"
                f"Le invio la mia candidatura per la posizione di "
                f"{fd.get('job_title', '')} presso {fd.get('company', '')}.\n"
            ),
            height=120,
        )

        st.markdown("---")

        # Preview
        with st.expander("👁️ Anteprima email"):
            letter_preview = st.session_state.generated_letter if include_letter else ""
            full_body = email_intro + "\n\n" + letter_preview if letter_preview else email_intro
            st.text(preview_email(to_email, email_subject, full_body, candidate.get("name","")))

        # Invio
        col_send, col_save = st.columns([1, 1])
        with col_send:
            send_btn = st.button("📧 Invia Candidatura", type="primary", use_container_width=True)
        with col_save:
            save_only = st.button("💾 Salva senza inviare", use_container_width=True)

        if send_btn:
            if not to_email:
                st.error("❌ Inserisci l'email del destinatario")
            elif not smtp_config["user"] or not smtp_config["password"]:
                st.error("❌ Configura le credenziali SMTP nella sidebar")
            else:
                letter_content = st.session_state.generated_letter if include_letter else ""
                full_body = email_intro + "\n\n" + letter_content if letter_content else email_intro

                with st.spinner("📤 Invio in corso…"):
                    ok, msg = send_email(
                        smtp_config=smtp_config,
                        to_email=to_email,
                        subject=email_subject,
                        body=full_body,
                        cv_file=cv_file,
                        cv_filename=cv_name,
                    )

                if ok:
                    st.success("✅ Candidatura inviata con successo!")
                    add_application(
                        job_title=fd.get("job_title", ""),
                        company=fd.get("company", ""),
                        location=fd.get("location", ""),
                        url=fd.get("job_url", ""),
                        hr_email=to_email,
                        cover_letter=st.session_state.generated_letter,
                        status="Inviata",
                    )
                    st.balloons()
                else:
                    st.error(f"❌ Errore: {msg}")

        if save_only:
            if not fd.get("job_title") or not fd.get("company"):
                st.error("❌ Compila almeno titolo e azienda nel tab '📋 1. Dettagli Offerta'")
            else:
                add_application(
                    job_title=fd.get("job_title",""),
                    company=fd.get("company",""),
                    location=fd.get("location",""),
                    url=fd.get("job_url",""),
                    hr_email=to_email,
                    cover_letter=st.session_state.generated_letter,
                    status="In revisione",
                )
                st.success("💾 Candidatura salvata nel tracker (stato: 'In revisione')")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    st.markdown("""
    <div class="sjh-header">
        <div>
            <h1>📊 Dashboard Candidature</h1>
            <p>Traccia lo stato di tutte le tue candidature</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    stats = get_stats()
    apps  = get_applications()

    # ── KPI ──────────────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    kpis = [
        (col1, stats["total"],     "📤 Totali"),
        (col2, stats["pending"],   "⏳ In Attesa"),
        (col3, stats["interviews"],"📞 Colloqui"),
        (col4, stats["offers"],    "🎉 Offerte"),
        (col5, stats["rejected"],  "❌ Rifiutate"),
    ]
    for col, val, label in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi">
                <div class="number">{val}</div>
                <div class="label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    if stats["total"] > 0:
        rate = round(stats["interviews"] / stats["total"] * 100, 1) if stats["total"] else 0
        st.markdown(f"<p class='hint' style='margin-top:.6rem'>Tasso colloqui: <b>{rate}%</b></p>",
                    unsafe_allow_html=True)

    st.markdown("---")

    if not apps:
        st.info("🚀 Nessuna candidatura ancora. Inizia dalla pagina '🔍 Cerca Offerte'!")
    else:
        # ── Filtri ────────────────────────────────────────────────────────
        col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
        with col_f1:
            status_filter = st.multiselect("Filtra per stato", STATUS_OPTIONS, default=[])
        with col_f2:
            company_filter = st.text_input("Filtra azienda", "")
        with col_f3:
            sort_by = st.selectbox("Ordina per", ["Data (recente)", "Azienda", "Stato"])

        df = pd.DataFrame(apps)
        if status_filter:
            df = df[df["status"].isin(status_filter)]
        if company_filter:
            df = df[df["company"].str.contains(company_filter, case=False, na=False)]
        if sort_by == "Azienda":
            df = df.sort_values("company")
        elif sort_by == "Stato":
            df = df.sort_values("status")

        st.markdown(f"<span class='hint'>{len(df)} candidature mostrate</span>", unsafe_allow_html=True)

        # ── Tabella ───────────────────────────────────────────────────────
        for _, row in df.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
                with c1:
                    st.markdown(f"**{row['job_title']}**  \n🏢 {row['company']} &nbsp;|&nbsp; 📍 {row.get('location','—')}")
                    if row.get("url"):
                        st.markdown(f"[🔗 Offerta]({row['url']})", unsafe_allow_html=False)
                with c2:
                    st.markdown(status_badge(row["status"]), unsafe_allow_html=True)
                    st.markdown(f"<span class='hint'>{row.get('sent_date','')[:10]}</span>",
                                unsafe_allow_html=True)
                with c3:
                    new_status = st.selectbox(
                        "Stato",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(row["status"]) if row["status"] in STATUS_OPTIONS else 0,
                        key=f"status_{row['id']}",
                        label_visibility="collapsed",
                    )
                    if new_status != row["status"]:
                        update_application_status(int(row["id"]), new_status)
                        st.rerun()
                with c4:
                    if st.button("🗑️", key=f"del_{row['id']}", help="Elimina"):
                        delete_application(int(row["id"]))
                        st.rerun()

                # Espandi storia e lettera
                with st.expander("📋 Dettagli & Storia"):
                    hist = get_status_history(int(row["id"]))
                    if hist:
                        st.markdown("**Cronologia stati:**")
                        for h in hist:
                            arrow = f"{h['old_status']} → {h['new_status']}" if h["old_status"] else h["new_status"]
                            st.markdown(f"- `{h['changed_at'][:16]}` — {arrow}"
                                        + (f" _{h['note']}_" if h.get("note") else ""))

                    if row.get("cover_letter"):
                        st.markdown("**Lettera di motivazione:**")
                        st.text_area("", value=row["cover_letter"], height=200,
                                     key=f"letter_{row['id']}", disabled=True)

                st.markdown("---")

        # ── Grafici ───────────────────────────────────────────────────────
        st.markdown("### 📈 Analisi")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("**Distribuzione per Stato**")
            status_df = df["status"].value_counts().reset_index()
            status_df.columns = ["Stato", "Conteggio"]
            st.bar_chart(status_df.set_index("Stato"))

        with col_g2:
            st.markdown("**Top Aziende**")
            comp_df = df["company"].value_counts().head(8).reset_index()
            comp_df.columns = ["Azienda", "Candidature"]
            st.bar_chart(comp_df.set_index("Azienda"))

        st.markdown("---")

        # ── Export ────────────────────────────────────────────────────────
        col_exp1, col_exp2 = st.columns([1, 4])
        with col_exp1:
            csv = export_to_csv()
            st.download_button(
                "⬇️ Esporta CSV",
                data=csv,
                file_name=f"candidature_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
