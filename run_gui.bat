@echo off
title ASE PDF Scraper - Universal GUI
echo.
echo 🎓 ASE PDF Scraper - Universal GUI
echo ==================================
echo.
echo This interface works for ALL ASE faculties!
echo Just select your faculty, program, and options.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python found. Installing requirements...
pip install requests beautifulsoup4 >nul 2>&1

echo.
echo 🚀 Starting Universal GUI...
echo.
python ase_gui_downloader.py

echo.
echo GUI closed. Press any key to exit.
pause >nul
