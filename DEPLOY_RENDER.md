# 🚀 Deploy su Render.com - Guida step-by-step

## ✅ Perché Render?
- **100% GRATIS** (no carta di credito)
- **Zero configurazione** (rileva tutto automaticamente)
- **SSL automatico** (HTTPS)
- **Deploy in 2 minuti**

---

## 📋 Step 1: Prepara le API Keys

Prima di deployare, ottieni queste chiavi (tutte gratuite):

### 1. Groq API Key (per lettere AI)
1. Vai su **[console.groq.com](https://console.groq.com)**
2. Sign up con Google
3. API Keys → Create API Key
4. Copia la key (inizia con `gsk_...`)

### 2. Adzuna API (per ricerca offerte - opzionale)
1. Vai su **[developer.adzuna.com](https://developer.adzuna.com)**
2. Register → Create new app
3. Copia **Application ID** e **Application Key**

---

## 🌐 Step 2: Deploy su Render

### A. Vai su Render
1. Apri **[render.com](https://render.com)**
2. Click **Get Started** → Sign up con GitHub
3. Autorizza Render ad accedere ai tuoi repo

### B. Crea Web Service
1. Nel dashboard Render, click **New +** → **Web Service**
2. Cerca e seleziona il repo **`bogaug/swiss-job-hunter`**
3. Click **Connect**

### C. Configurazione (auto-rilevata da render.yaml)
Render rileva automaticamente:
- ✅ **Name**: `swiss-job-hunter`
- ✅ **Build Command**: `pip install -r requirements.txt`
- ✅ **Start Command**: `python start.py`
- ✅ **Python Version**: 3.11

**NON modificare nulla** — click **Create Web Service**

### D. Aggiungi variabili d'ambiente
Mentre il deploy è in corso:

1. Nel menu laterale → **Environment**
2. Click **Add Environment Variable** per ciascuna:

   | Key | Value | Note |
   |---|---|---|
   | `GROQ_API_KEY` | `gsk_...` | La tua key Groq (obbligatoria) |
   | `ADZUNA_APP_ID` | `xxxxx` | Opzionale — migliora ricerca |
   | `ADZUNA_APP_KEY` | `xxxxx` | Opzionale |

3. Click **Save Changes**

---

## ✅ Step 3: App è LIVE!

Dopo ~2 minuti vedrai:

```
==> Build successful 🎉
==> Deploying...
==> Your service is live at https://swiss-job-hunter-XXXX.onrender.com
```

**Copia questo URL** — è il tuo link permanente!

---

## 📱 Step 4: Installa su Android

### Dal telefono:

1. Apri **Chrome**
2. Vai al tuo URL Render (es: `https://swiss-job-hunter-xxxx.onrender.com`)
3. Menu **⋮** (3 pallini) → **"Aggiungi a schermata Home"**
4. Conferma → l'icona 🇨🇭 **Swiss Job Hunter** appare sulla home

**L'app è ora installata!** Funziona come un'app nativa:
- ✅ Si apre a schermo intero (no barra browser)
- ✅ Funziona offline dopo il primo caricamento
- ✅ Icona sulla home come le altre app

---

## ⚙️ Configurazione nell'app

Dopo aver aperto l'app (web o mobile):

1. Vai su **Impostazioni** (icona ingranaggio in basso a destra)
2. Compila il tuo profilo candidato:
   - Nome completo
   - Email
   - Competenze
   - Formazione
   - Lingue

3. **API Keys** (già configurate lato server, ma se vuoi cambiarle):
   - Sono opzionali nell'app — il server usa quelle configurate su Render

4. **Email SMTP** (per inviare candidature):
   - SMTP Host: `smtp.gmail.com`
   - Porta: `587`
   - Email mittente: la tua Gmail
   - App Password: [Genera qui](https://myaccount.google.com/apppasswords)
     - Attiva 2FA su Gmail
     - Genera App Password per "Mail"
     - Copia password di 16 caratteri (formato: `xxxx xxxx xxxx xxxx`)

5. Click **💾 Salva tutto**

---

## 🎯 Utilizzo

### 1️⃣ Cerca Offerte
- Tab **Cerca** → inserisci parole chiave (es: "Data Engineer")
- Seleziona regione
- Click **Cerca**

**Modalità demo** (senza Adzuna key):
- Mostra 5 offerte di esempio per testare l'interfaccia
- Per risultati reali: configura Adzuna keys su Render

### 2️⃣ Candidati
- Click **✍️ Candidati** su un'offerta
- Compila dettagli → Click **💾 Salva**
- Tab **🤖 Lettera AI** → Click **Genera Lettera**
- Modifica se necessario → Tab **📧 Invia**
- Verifica destinatario → Click **📧 Invia**

### 3️⃣ Dashboard
- Tab **Dashboard** → vedi tutte le candidature
- KPI: Totali, Colloqui, Offerte
- Aggiorna stato con dropdown
- Esporta CSV

---

## 🔧 Troubleshooting

### ❌ "Application Error" su Render
**Causa:** Variabili d'ambiente mancanti o errore build  
**Fix:**
1. Environment → verifica `GROQ_API_KEY` sia presente
2. Logs → cerca errori
3. Redeploy: Manual Deploy → Deploy latest commit

### ❌ Ricerca non funziona (modalità demo sempre attiva)
**Causa:** Adzuna keys non configurate  
**Fix:**
1. Ottieni keys su [developer.adzuna.com](https://developer.adzuna.com)
2. Render → Environment → Aggiungi `ADZUNA_APP_ID` e `ADZUNA_APP_KEY`
3. Riavvia app

### ❌ Generazione lettera fallisce
**Causa:** Groq API key invalida o mancante  
**Fix:**
1. Verifica key su [console.groq.com](https://console.groq.com)
2. Render → Environment → Aggiorna `GROQ_API_KEY`
3. Salva changes

### ❌ Email non invia
**Causa:** SMTP non configurato o App Password errata  
**Fix:**
1. Gmail: usa **App Password** (non password normale)
2. [Genera qui](https://myaccount.google.com/apppasswords)
3. Nell'app → Impostazioni → Email SMTP → inserisci password 16 caratteri

### ⚠️ App si "addormenta" dopo 15 min
**Normale su Render free tier:**
- Prima richiesta dopo inattività: ~30 secondi
- Poi veloce come sempre
- **Nessun costo**, solo un po' di pazienza

---

## 💰 Costi

**ZERO €** — completamente gratis:
- ✅ Render free tier: 750 ore/mese (più che sufficienti)
- ✅ Groq API: gratuita
- ✅ Adzuna API: 250 richieste/giorno gratis
- ✅ Gmail SMTP: gratis

**Unico limite:** cold start di 30 sec dopo 15 min inattività (accettabile!)

---

## 📊 Database persistenza

⚠️ **Importante:** Il database SQLite su Render free tier **non è persistente** al redeploy.

**Soluzioni:**

### Opzione 1: Render Disk (consigliata - gratis)
1. Render dashboard → tua app
2. **Disks** → **Add Disk**
3. Mount Path: `/data`
4. Size: 1 GB (gratis)
5. Aggiungi variabile d'ambiente:
   - Key: `DB_PATH`
   - Value: `/data/applications.db`

### Opzione 2: Export periodico CSV
- Dashboard → **⬇️ Esporta CSV** prima di ogni redeploy
- Backup manuale

---

## 🎉 Done!

L'app è ora:
- ✅ Online 24/7
- ✅ Accessibile da qualsiasi dispositivo
- ✅ Installabile come app nativa su Android
- ✅ Completamente gratuita

**URL finale:** `https://swiss-job-hunter-XXXX.onrender.com`

Buona caccia al lavoro! 🇨🇭🚀
