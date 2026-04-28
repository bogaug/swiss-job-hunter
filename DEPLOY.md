# 📱 Deploy gratuito su smartphone

Scegli **una** di queste opzioni per avere l'app sempre online e accessibile da qualsiasi smartphone.

---

## ✅ Opzione 1: Render.com (PIÙ SEMPLICE)

**Pro:** Deploy automatico da GitHub, nessun comando da terminale
**Contro:** Server si spegne dopo 15 min inattività (si riavvia al primo accesso, ~30 sec)

### Passi:

1. **Vai su [render.com](https://render.com)** → Sign up con GitHub
2. **New +** → **Web Service**
3. **Connect repository:** seleziona `bogaug/swiss-job-hunter`
4. Configurazione automatica (Render legge `render.yaml`)
5. Clicca **"Create Web Service"**
6. Aspetta 2-3 minuti → otterrai un URL tipo:
   ```
   https://swiss-job-hunter.onrender.com
   ```

7. **Apri l'URL sul telefono** → Chrome → Menu ⋮ → **"Installa app"**

✅ Fatto! L'app si aggiorna automaticamente ad ogni push su GitHub.

---

## ✅ Opzione 2: Railway.app (SEMPRE ATTIVO)

**Pro:** Server sempre attivo, velocissimo
**Contro:** 500 ore/mese gratis (~16 ore/giorno), poi $5/mese

### Passi:

1. **Installa Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login e deploy:**
   ```bash
   cd swiss-job-hunter
   railway login
   railway init
   railway up
   ```

3. **Ottieni l'URL pubblico:**
   ```bash
   railway domain
   ```
   
   Ti dà un URL tipo: `swiss-job-hunter-production.up.railway.app`

4. **Apri sul telefono** → installa come PWA

---

## ✅ Opzione 3: Fly.io (500 ORE/MESE GRATIS)

**Pro:** Sempre attivo, datacenter EU (Amsterdam)
**Contro:** Richiede carta di credito (non viene addebitato nulla)

### Passi:

1. **Installa Fly CLI:**
   ```bash
   # Mac
   brew install flyctl
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Signup e deploy:**
   ```bash
   cd swiss-job-hunter
   fly auth signup
   fly launch --no-deploy
   # Seleziona: Amsterdam (ams), conferma tutto
   fly deploy
   ```

3. **L'URL sarà:**
   ```
   https://swiss-job-hunter.fly.dev
   ```

---

## 🆓 Opzione 4: Vercel (LIMITI STRETTI)

**Pro:** Deploy istantaneo, sempre attivo
**Contro:** Non supporta API persistenti (solo serverless), database SQLite non funziona

❌ **Non consigliato** per questa app (serve database persistente)

---

## 🎯 Quale scegliere?

| Piattaforma | Tempo setup | Sempre attivo | Database | Consigliato per |
|---|---|---|---|---|
| **Render.com** | ⭐⭐⭐⭐⭐ 2 min | ❌ (dorme) | ✅ | Uso personale |
| **Railway.app** | ⭐⭐⭐⭐ 5 min | ✅ 500h/mese | ✅ | Uso frequente |
| **Fly.io** | ⭐⭐⭐ 10 min | ✅ 500h/mese | ✅ | Produzione |

---

## 📲 Dopo il deploy

1. Apri l'URL sul tuo **Android** con **Chrome**
2. Menu **⋮** → **"Aggiungi a schermata Home"**
3. L'icona 🇨🇭 apparirà sulla home
4. L'app funziona come un'app nativa:
   - ✅ Offline (dopo prima apertura)
   - ✅ Notifiche (se abilitate)
   - ✅ Fullscreen
   - ✅ Veloce come app nativa

---

## 🔧 Variabili d'ambiente

Per configurare API keys sul server (sicuro, non visibili nel codice):

**Render.com:**
Dashboard → Environment → Add Variable:
```
GROQ_API_KEY=gsk_...
ADZUNA_APP_ID=...
ADZUNA_APP_KEY=...
```

**Railway:**
```bash
railway variables set GROQ_API_KEY=gsk_...
```

**Fly.io:**
```bash
fly secrets set GROQ_API_KEY=gsk_...
```

---

## 🚀 La mia raccomandazione

**Per te consiglio Render.com:**
- ✅ 2 minuti di setup (zero comandi)
- ✅ Deploy automatico ad ogni push GitHub
- ✅ Database SQLite persistente
- ✅ HTTPS gratuito
- ✅ Nessuna carta richiesta

Il fatto che si spenga dopo 15 min è OK — si risveglia in ~30 secondi al primo accesso.
