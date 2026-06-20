@echo off
setlocal enabledelayedexpansion
title PDF Renamer - Build Script

echo ================================================
echo   PDF Renamer  ^|  Windows EXE Builder
echo ================================================
echo.

REM ── Step 1: Find or auto-install Python ──────────
set "PYEXE="

REM Check if python is already on PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYEXE=python"
    goto :python_found
)

REM Check common per-user install locations (Python 3.9 - 3.12)
for %%V in (312 311 310 39) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :python_found
    )
)

REM Check system-wide install locations
for %%V in (312 311 310 39) do (
    if exist "C:\Python%%V\python.exe" (
        set "PYEXE=C:\Python%%V\python.exe"
        goto :python_found
    )
)

REM ── Python not found: download and install it ─────
echo Python not found on this machine.
echo Downloading Python 3.11.9 installer (this requires internet access)...
echo.

powershell -NoProfile -Command ^
  "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe' -UseBasicParsing"

if errorlevel 1 (
    echo ERROR: Could not download Python installer.
    echo        Check your internet connection, then install manually:
    echo        https://python.org/downloads/
    pause & exit /b 1
)

echo Installing Python 3.11 for current user (silent install)...
REM /quiet          = no UI
REM InstallAllUsers=0  = current user only (no admin rights needed)
REM PrependPath=1   = adds Python to PATH environment variable
REM Include_test=0  = skip test suite to save space
"%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Shortcuts=0 Include_test=0 Include_launcher=0

REM Use the known install path directly (PATH refresh not needed)
set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"

if not exist "!PYEXE!" (
    echo ERROR: Python installed but not found at expected path.
    echo        Please close this window, reopen it, and run the script again.
    pause & exit /b 1
)

echo Python installed successfully.
echo NOTE: PATH will be active in new terminal windows automatically.
echo.

:python_found
echo Using: !PYEXE!
"!PYEXE!" --version
echo.

REM ── Step 2: Install Python packages ──────────────
echo [1/3] Installing build dependencies (pdfplumber, PyPDF2, pyinstaller)...
"!PYEXE!" -m pip install --upgrade pip --quiet
"!PYEXE!" -m pip install pdfplumber PyPDF2 "pyinstaller>=6.0.0"
if errorlevel 1 (
    echo ERROR: pip install failed. Check your internet connection and try again.
    pause & exit /b 1
)
echo.

REM ── Step 3: Build the exe ─────────────────────────
echo [2/3] Building PDF Renamer.exe (takes 1-3 minutes)...
"!PYEXE!" -m PyInstaller pdf_renamer.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed. See output above for details.
    pause & exit /b 1
)
echo.

REM ── Result ────────────────────────────────────────
echo [3/3] Verifying output...
if exist "dist\PDF Renamer.exe" (
    echo.
    echo ================================================
    echo   BUILD SUCCESSFUL
    echo ================================================
    echo.
    echo   File: dist\PDF Renamer.exe
    for %%F in ("dist\PDF Renamer.exe") do echo   Size: %%~zF bytes
    echo.
    echo   Copy this single .exe to any Windows PC.
    echo   Recipients need NO Python or other software.
    echo.
    echo   OPTIONAL: Open installer.iss in Inno Setup to
    echo   build a proper Windows installer (.exe setup).
) else (
    echo ERROR: dist\PDF Renamer.exe was not created. Check output above.
)

echo.
pause
