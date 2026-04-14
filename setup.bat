@echo off
echo ============================================
echo   NPC Actor System - Setup Script
echo ============================================
echo.

:: Check Python
python --version 2>NUL
if ERRORLEVEL 1 (
    echo [ERROR] Python not found! Install Python 3.11+ first.
    pause
    exit /b 1
)

:: Create virtual environment
echo [1/4] Creating virtual environment...
python -m venv venv
if ERRORLEVEL 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

:: Activate and install dependencies
echo [2/4] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

:: Create .env file if it doesn't exist
echo [3/4] Setting up environment...
if not exist .env (
    copy .env.example .env
    echo.
    echo =============================================
    echo  IMPORTANT: You need to add your Gemini API key!
    echo  Edit the .env file and set GEMINI_API_KEY
    echo  Get a free key at: https://aistudio.google.com/apikey
    echo =============================================
    echo.
)

echo [4/4] Setup complete!
echo.
echo To run the application:
echo   call venv\Scripts\activate.bat
echo   python -m uvicorn backend.app:app --host 0.0.0.0 --port 8080 --reload
echo.
echo Then open: http://localhost:8080
echo.
pause
