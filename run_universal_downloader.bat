@echo off
echo ASE PDF Downloader - Universal Version
echo ======================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Python found. Installing required packages...
pip install -r requirements.txt

echo.
echo Starting universal PDF download...
python ase_universal_downloader.py

echo.
echo Script completed. Press any key to exit.
pause >nul
