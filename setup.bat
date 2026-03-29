@echo off
REM Quick setup script for Windows

echo ========================================
echo Qt for HarmonyOS Installer Setup
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.12 or later from: https://python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Check pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo [OK] pip found
pip --version

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed

REM Install the tool
echo.
echo Installing qtohos-installer...
pip install -e .

if errorlevel 1 (
    echo [ERROR] Failed to install qtohos-installer
    pause
    exit /b 1
)

echo [OK] qtohos-installer installed

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo You can now run:
echo   qtohos-installer install    - Start interactive installation
echo   qtohos-installer check      - Check prerequisites
echo   qtohos-installer guide      - Show installation guide
echo   qtohos-installer --help     - Show all commands
echo.
pause