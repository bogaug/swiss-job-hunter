# 📱 Deploy gratis su cloud (accessibile da smartphone)

## ⚡ Opzione 1: Render.com (Consigliata - più semplice)

**Setup in 3 click:**

1. Vai su **[render.com](https://render.com)** → Sign Up (gratis, no carta)
2. Click **New** → **Web Service**
3. Connetti GitHub → seleziona `bogaug/swiss-job-hunter`
4. Render rileva `render.yaml` automaticamente → **Create Web Service**
5. ✅ Dopo ~2 minuti hai l'URL: `https://swiss-job-hunter-XXXX.onrender.com`

**Aggiungi le tue API keys** (click su "Environment" nel dashboard):
- `GROQ_API_KEY` → [console.groq.com](https://console.groq.com)
- `ADZUNA_APP_ID` → [developer.adzuna.com](https://developer.adzuna.com)
- `ADZUNA_APP_KEY` → idem

**Limiti free tier:**
- ✅ Sempre online, HTTPS automatico
- ⚠️ Si addormenta dopo 15 min inattività (primo caricamento ~30 sec poi veloce)
- ✅ 750 ore/mese gratis

---

## ⚡ Opzione 2: Railway.app (Più veloce)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login e deploy
railway login
cd swiss-job-hunter
railway init
railway up
```

**Aggiungi variabili:**
```bash
railway variables set GROQ_API_KEY=gsk_xxx
railway variables set ADZUNA_APP_ID=xxx
railway variables set ADZUNA_APP_KEY=xxx
```

**Limiti free tier:**
- ✅ $5/mese crediti gratis (~500 ore)
- ✅ Più veloce (no cold start)

---

## ⚡ Opzione 3: Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
cd swiss-job-hunter
fly launch --name swiss-job-hunter
fly deploy
```

**Limiti free tier:**
- ✅ 3 app gratuite
- ✅ Cold start minimo

---

## 📱 Installazione PWA su Android

Dopo il deploy, dal telefono:

1. **Chrome** → vai al tuo URL (es: `https://swiss-job-hunter.onrender.com`)
2. Menu **⋮** (3 pallini) → **"Aggiungi a schermata Home"** / **"Installa app"**
3. ✅ L'icona 🇨🇭 appare sulla home — funziona come app nativa!

**Features:**
- ✅ Funziona offline (dopo prima apertura)
- ✅ Notifiche push (opzionale)
- ✅ Navigazione nativa Android
- ✅ Nessun App Store necessario

---

## 🔐 Sicurezza database

Il database SQLite è salvato nel filesystem del container. Per persistenza garantita usa:

**Render:** aggiungi un [Render Disk](https://render.com/docs/disks) (gratis fino a 1GB)
**Railway:** i [Volumes](https://docs.railway.app/guides/volumes) sono inclusi
**Fly:** usa [Fly Volumes](https://fly.io/docs/reference/volumes/)

Altrimenti il DB si resetta al redeploy (ok per test, non per produzione).
