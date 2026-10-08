@echo off
REM ============================================================
REM  ZSolution - Installation Script
REM  Creates Python 3.12 venv and installs all requirements.
REM  Portable: uses relative path (script's own folder)
REM ============================================================

setlocal

REM --- مسیر پروژه = پوشه‌ای که این فایل در آن است ---
set "PROJECT_DIR=%~dp0"
REM حذف backslash انتهایی
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

set "VENV_DIR=%PROJECT_DIR%\.venv"
set "REQ_FILE=%PROJECT_DIR%\requirements.txt"

echo.
echo ============================================================
echo   ZSolution - Environment Setup
echo ============================================================
echo.

REM --- بررسی پوشه پروژه ---
if not exist "%PROJECT_DIR%" (
    echo [ERROR] Project directory not found:
    echo         %PROJECT_DIR%
    pause
    exit /b 1
)
cd /d "%PROJECT_DIR%"
echo [OK] Project directory: %CD%
echo.

REM --- بررسی requirements.txt ---
if not exist "%REQ_FILE%" (
    echo [ERROR] requirements.txt not found in %PROJECT_DIR%
    pause
    exit /b 1
)
echo [OK] requirements.txt found.
echo.

REM --- بررسی مدل Vosk ---
set "VOSK_PATH=%PROJECT_DIR%\vosk\vosk-model-fa-0.5\vosk-model-fa-0.5"
if not exist "%VOSK_PATH%" (
    echo [WARN] Vosk model not found at:
    echo        %VOSK_PATH%
    echo        Please download and extract before running.
) else (
    echo [OK] Vosk model found.
)
echo.

REM --- بررسی مدل TTS ---
set "TTS_PATH=%PROJECT_DIR%\pocket-tts-farsi-v2\model.yaml"
if not exist "%TTS_PATH%" (
    echo [WARN] TTS model not found at:
    echo        %TTS_PATH%
) else (
    echo [OK] TTS model found.
)
echo.

REM --- بررسی FFmpeg ---
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [WARN] FFmpeg not found in PATH.
    echo        Install from https://ffmpeg.org/download.html
) else (
    echo [OK] FFmpeg found.
)
echo.

REM --- بررسی Python 3.12 ---
echo [1/6] Checking Python 3.12 ...
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.12 not found.
    echo         Install from https://www.python.org/downloads/
    pause
    exit /b 1
)
py -3.12 --version
echo.

REM --- ساخت venv ---
echo [2/6] Creating virtual environment ...
if exist "%VENV_DIR%" (
    echo [WARN] .venv already exists - skipping creation.
) else (
    py -3.12 -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)
echo.

REM --- فعال‌سازی venv ---
echo [3/6] Activating venv ...
call "%VENV_DIR%\Scripts\activate.bat"
echo [OK] VIRTUAL_ENV = %VIRTUAL_ENV%
echo.

REM --- آپدیت pip ---
echo [4/6] Upgrading pip ...
python -m pip install --upgrade pip
echo.

REM --- نصب requirements ---
echo [5/6] Installing requirements ...
pip install -r "%REQ_FILE%"
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo.

REM --- نصب Vosk wheel ---
echo [6/6] Installing Vosk prebuilt wheel ...
pip install https://github.com/alphacep/vosk-api/releases/download/v0.3.42/vosk-0.3.42-py3-none-win_amd64.whl
if errorlevel 1 (
    echo [WARN] Vosk wheel install failed. It may already be installed.
)
echo.

echo ============================================================
echo   Installation finished successfully!
echo ============================================================
echo   Activate later:  .venv\Scripts\activate
echo   Run the app   :  run.bat
echo ============================================================
echo.

endlocal
pause