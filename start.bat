@echo off
echo ========================================
echo Quiz-Master App starten
echo ========================================
echo.

REM Prüfen ob Backend bereits läuft und beenden
echo [VORBEREITUNG] Alte Backend-Prozesse werden beendet...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Beende Prozess %%a auf Port 8000...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM Backend zuerst starten
echo [1/3] Backend wird gestartet...
start "Quiz-Master Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul

REM Prüfen ob Backend läuft
echo [2/3] Pruefe Backend...
curl -s http://localhost:8000/events >nul 2>&1
if %errorlevel% neq 0 (
    echo FEHLER: Backend ist nicht erreichbar!
    echo Bitte pruefen ob Python installiert ist.
    pause
    exit /b 1
)
echo Backend lauft auf http://localhost:8000

REM Alte Frontend-Prozesse beenden
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    echo Beende Prozess %%a auf Port 5173...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM Frontend starten
echo [3/3] Frontend wird gestartet...
cd /d %~dp0frontend
start "Quiz-Master Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo App ist jetzt erreichbar:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo ========================================
echo.
echo Schliese die Fenster um die App zu stoppen.
pause
