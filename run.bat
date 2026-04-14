@echo off
echo ============================================
echo   NPC Actor System - Run Server
echo ============================================
echo.

call venv\Scripts\activate.bat

echo Starting server at http://localhost:8080
echo.
echo  Dashboard:  http://localhost:8080
echo  Earpiece:   http://localhost:8080/actor
echo  Scanner:    http://localhost:8080/scanner
echo.
echo Press Ctrl+C to stop the server.
echo.

python -m uvicorn backend.app:app --host 0.0.0.0 --port 8080 --reload
