@echo off
echo ===================================================
echo     EduSynergy - Quick Start Guide
echo ===================================================
echo.

:: 1. Start Backend
echo [1/3] Installing Python dependencies and starting backend...
cd backend
call pip install -r requirements.txt
call playwright install chromium

start "AI Backend (FastAPI)" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000"
cd ..

echo.
:: 2. Start Frontend
echo [2/3] Installing Node.js dependencies and starting frontend...
cd frontend
call npm install

start "AI Frontend (Vue3)" cmd /k "npm run dev"
cd ..

echo.
:: 3. Launch Browser
echo [3/3] Services are starting. Please wait...
timeout /t 4 /nobreak >nul

start http://localhost:5173

echo.
echo [SUCCESS] All services are running! 
echo To stop the servers, just close the two new CMD windows.
pause