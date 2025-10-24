#!/usr/bin/env python3
"""
Build script to create standalone .exe for ASE PDF Scraper
Run this to generate ASE_PDF_Scraper.exe
"""

import os
import sys
import subprocess

def main():
    print("=" * 60)
    print("ASE PDF Scraper - EXE Build Script")
    print("=" * 60)

    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("[OK] PyInstaller found")
    except ImportError:
        print("[!] PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed")

    # Build the executable
    print("\nBuilding executable...")

    cmd = [
        "pyinstaller",
        "--onefile",                          # Single .exe file
        "--windowed",                         # No console window (GUI only)
        "--name=ASE_PDF_Scraper",            # Output filename
        "--icon=NONE",                        # No icon (could add one later)
        "--add-data=requirements.txt;.",      # Include requirements for reference
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.scrolledtext",
        "--hidden-import=requests",
        "--hidden-import=bs4",
        "--hidden-import=lxml",
        "--clean",                            # Clean build
        "ase_gui_downloader.py"
    ]

    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 60)
        print("[OK] Build successful!")
        print("=" * 60)
        print(f"\nExecutable created: dist/ASE_PDF_Scraper.exe")
        print("\nYou can now distribute this single .exe file to students.")
        print("No Python or dependencies needed - just run it!")

    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
