# 🇨🇭 Swiss Job Hunter

**Streamlit app per cercare offerte di lavoro in Svizzera, generare lettere di motivazione con AI e tracciare le candidature.**

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red)
![Anthropic](https://img.shields.io/badge/Claude-AI-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Funzionalità

| Feature | Dettaglio |
|---|---|
| 🔍 **Ricerca offerte** | Scraping su `jobs.ch` e `jobup.ch` per regione svizzera |
| 🤖 **Lettera AI** | Generazione lettera di motivazione personalizzata con Claude |
| 📧 **Invio email** | Invio automatico via SMTP (Gmail, Outlook, Proton Mail…) |
| 📊 **Dashboard** | Tracking candidature con stati, cronologia e grafici |
| 🌍 **Multilingua** | Lettere in Francese, Italiano, Inglese, Tedesco |
| ⬇️ **Export CSV** | Esporta le tue candidature per analisi esterne |

---

## 🚀 Avvio rapido

### 1. Clona il repository

```bash
git clone https://github.com/bogaug/swiss-job-hunter.git
cd swiss-job-hunter
```

### 2. Crea ambiente virtuale e installa dipendenze

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

### 3. Configura le variabili d'ambiente

```bash
cp .env.example .env
# Modifica .env con il tuo editor preferito
```

Variabili necessarie:

| Variabile | Descrizione |
|---|---|
| `ANTHROPIC_API_KEY` | Key da [console.anthropic.com](https://console.anthropic.com) |
| `CANDIDATE_NAME` | Il tuo nome completo |
| `CANDIDATE_EMAIL` | La tua email |
| `SMTP_USER` | Email mittente |
| `SMTP_PASSWORD` | App Password SMTP |

> **Gmail:** vai su [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) per generare un'App Password (richiede 2FA attivo).

### 4. Avvia l'app

```bash
streamlit run app.py
```

L'app si aprirà automaticamente su `http://localhost:8501`.

---

## 📁 Struttura progetto

```
swiss-job-hunter/
├── app.py                  # App principale Streamlit
├── modules/
│   ├── __init__.py
│   ├── scraper.py          # Scraping jobs.ch / jobup.ch
│   ├── ai_generator.py     # Generazione lettere con Claude
│   ├── email_sender.py     # Invio SMTP
│   └── tracker.py          # Database SQLite candidature
├── data/                   # Database SQLite (gitignored)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🔍 Scraping — Note tecniche

Il scraper prova le seguenti strategie in ordine:

1. **API interna** — endpoint JSON nativo del sito
2. **`__NEXT_DATA__`** — estrazione dati da tag `<script id="__NEXT_DATA__">` (siti Next.js)
3. **HTML parsing** — CSS selectors con BeautifulSoup

> ⚠️ **Nota:** `jobs.ch` e `jobup.ch` possono implementare protezioni anti-bot. Se la ricerca non produce risultati, incolla manualmente il testo dell'offerta nella tab "Dettagli Offerta" — tutte le altre funzionalità (generazione AI, invio, tracking) funzionano perfettamente lo stesso.

**Regioni supportate:**

- Svizzera Romanda (FR/GE/VD/VS/NE/JU)
- Ticino (TI)
- Zurigo (ZH)
- Berna (BE)
- Basilea (BS/BL)
- Svizzera Centrale
- Svizzera Orientale
- Tutta la Svizzera

---

## 🤖 Generazione lettera con AI

La lettera viene generata da **Claude** (Anthropic) seguendo le convenzioni epistolari svizzere. Il prompt include:

- Titolo posizione e azienda
- Descrizione dell'offerta (se fornita — altamente consigliato)
- Il tuo profilo (skills, formazione, esperienze)
- Note personalizzate (opzionale)

**Modelli disponibili:**
- `claude-opus-4-5` — qualità massima (consigliato per candidature importanti)
- `claude-sonnet-4-6` — ottimo equilibrio qualità/costo
- `claude-haiku-4-5` — veloce ed economico

---

## 📊 Dashboard tracking

Ogni candidatura registra:
- Titolo, azienda, luogo, URL, email HR
- Stato attuale (con cronologia completa)
- Lettera di motivazione generata
- Data invio e note

**Stati disponibili:** Inviata → In revisione → Colloquio telefonico → Colloquio in presenza → Assessment → Offerta ricevuta → Accettata / Rifiutata / Ritirata

---

## 🔒 Privacy

- Il database SQLite è salvato localmente in `/data/` (gitignored)
- Le credenziali SMTP e API key sono nel `.env` (gitignored)
- Nessun dato viene inviato a server esterni (eccetto le API Anthropic)

---

## 📄 Licenza

MIT License — libero per uso personale e commerciale.

---

*Sviluppato con ❤️ per il mercato del lavoro svizzero*
