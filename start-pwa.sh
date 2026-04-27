#!/bin/bash
# start-pwa.sh - Avvia Swiss Job Hunter PWA

echo "🇨🇭 Swiss Job Hunter - Avvio PWA..."
echo ""

# Trova IP locale
if [[ "$OSTYPE" == "darwin"* ]]; then
    IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    IP=$(hostname -I | awk '{print $1}')
else
    IP=$(ipconfig | grep "IPv4" | head -1 | awk '{print $NF}')
fi

echo "📱 Accedi dall'app dal tuo telefono Android:"
echo ""
echo "   http://${IP}:8000"
echo ""
echo "   1. Apri Chrome sul telefono"
echo "   2. Vai all'URL sopra"
echo "   3. Menu ⋮ → 'Installa app'"
echo ""
echo "📊 Dashboard Streamlit (desktop):"
echo "   http://localhost:8501"
echo ""
echo "────────────────────────────────────────"
echo "Server in avvio..."
echo ""

# Avvia in parallelo FastAPI (PWA) e Streamlit (desktop)
uvicorn api:app --host 0.0.0.0 --port 8000 &
PID_API=$!

streamlit run app.py --server.port 8501 --server.headless true &
PID_STREAMLIT=$!

echo ""
echo "✅ Server attivi!"
echo ""
echo "Premi CTRL+C per fermare"
echo ""

# Trap per chiudere entrambi
trap "kill $PID_API $PID_STREAMLIT 2>/dev/null; exit" INT TERM

wait
