@echo off
echo ============================================
echo   FinOps Agentic Copilot v2.0
echo   Starting Backend + Frontend...
echo ============================================
echo.

:: Start FastAPI backend
echo [1/2] Starting FastAPI backend on port 8000...
start "FinOps-Backend" cmd /c "cd /d %~dp0 && python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for backend to be ready
timeout /t 3 /nobreak > nul

:: Start React frontend
echo [2/2] Starting React frontend on port 5173...
start "FinOps-Frontend" cmd /c "cd /d %~dp0\frontend && npm run dev"

echo.
echo ============================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Press any key to stop both servers...
pause > nul

:: Kill both
taskkill /FI "WINDOWTITLE eq FinOps-Backend" /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq FinOps-Frontend" /F > nul 2>&1
