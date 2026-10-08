@echo off
REM ============================================================
REM  ZSolution - Run Script
REM  Activates venv and launches the app
REM  Portable: uses relative path (script's own folder)
REM ============================================================

setlocal

REM --- مسیر پروژه = پوشه‌ای که این فایل در آن است ---
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

set "VENV_DIR=%PROJECT_DIR%\.venv"
set "APP_FILE=%PROJECT_DIR%\zsolution_init.py"

echo.
echo ============================================================
echo   ZSolution - Launching Application
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

REM --- بررسی venv ---
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at:
    echo         %VENV_DIR%
    echo.
    echo         Please run install.bat first.
    pause
    exit /b 1
)

REM --- بررسی فایل اصلی ---
if not exist "%APP_FILE%" (
    echo [ERROR] Main file not found:
    echo         %APP_FILE%
    pause
    exit /b 1
)

REM --- فعال‌سازی venv ---
echo [OK] Activating venv...
call "%VENV_DIR%\Scripts\activate.bat"

REM --- بررسی FFmpeg ---
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [WARN] FFmpeg not found in PATH - STT may not work for WebM files.
)

echo [OK] Starting ZSolution...
echo.
echo ============================================================
echo   Server will be available at: http://127.0.0.1:7862
echo   Press Ctrl+C to stop
echo ============================================================
echo.

REM --- اجرا ---
python "%APP_FILE%"

REM --- اگر برنامه خطا داد، پنجره باز بماند ---
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error code %errorlevel%
    pause
)

endlocal