@echo off
REM start-pwa.bat - Avvia Swiss Job Hunter PWA (Windows)

echo 🇨🇭 Swiss Job Hunter - Avvio PWA...
echo.

REM Trova IP locale
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%

echo 📱 Accedi dall'app dal tuo telefono Android:
echo.
echo    http://%IP%:8000
echo.
echo    1. Apri Chrome sul telefono
echo    2. Vai all'URL sopra
echo    3. Menu ⋮ → 'Installa app'
echo.
echo 📊 Dashboard Streamlit (desktop):
echo    http://localhost:8501
echo.
echo ────────────────────────────────────────
echo Server in avvio...
echo.

REM Avvia FastAPI (PWA)
start "FastAPI" cmd /k uvicorn api:app --host 0.0.0.0 --port 8000

REM Avvia Streamlit (desktop)
start "Streamlit" cmd /k streamlit run app.py --server.port 8501

echo.
echo ✅ Server attivi!
echo.
echo Chiudi le finestre per fermare i server
pause
