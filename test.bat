@echo off
echo ============================================
echo   NPC Actor System - Run Tests
echo ============================================
echo.

call venv\Scripts\activate.bat

echo Running tests with coverage...
echo.

pytest backend\tests\ -v --cov=backend --cov-report=term-missing

echo.
pause
