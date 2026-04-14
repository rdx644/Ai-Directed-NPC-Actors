@echo off
echo ============================================
echo   NPC Actor System - Deploy to Cloud Run
echo ============================================
echo.

:: Check if gcloud is installed
gcloud --version 2>NUL
if ERRORLEVEL 1 (
    echo [ERROR] Google Cloud SDK not found!
    echo Download from: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

:: Get project ID
echo.
echo Current GCP project:
gcloud config get-value project
echo.

:: Prompt for Gemini API key
set /p GEMINI_KEY="Enter your Gemini API Key: "
if "%GEMINI_KEY%"=="" (
    echo [ERROR] Gemini API key is required!
    pause
    exit /b 1
)

echo.
echo [1/3] Building and deploying to Cloud Run...
echo This may take 3-5 minutes...
echo.

:: Deploy directly from source (simplest method)
gcloud run deploy npc-actor-system ^
    --source . ^
    --region us-central1 ^
    --platform managed ^
    --allow-unauthenticated ^
    --port 8080 ^
    --memory 512Mi ^
    --cpu 1 ^
    --min-instances 0 ^
    --max-instances 3 ^
    --set-env-vars "GEMINI_API_KEY=%GEMINI_KEY%,APP_ENV=production,DATABASE_MODE=memory,TTS_MODE=browser"

if ERRORLEVEL 1 (
    echo.
    echo [ERROR] Deployment failed!
    echo Make sure you have:
    echo   1. A GCP project set: gcloud config set project YOUR_PROJECT_ID
    echo   2. Cloud Run API enabled: gcloud services enable run.googleapis.com
    echo   3. Billing enabled on the project
    echo   4. Artifact Registry API: gcloud services enable artifactregistry.googleapis.com
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Deployment successful!
echo ============================================
echo.
echo Your Cloud Run URL will be displayed above.
echo.
pause
