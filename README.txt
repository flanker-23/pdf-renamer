PDF RENAMER - Windows Standalone Application
=============================================

WHAT IT DOES
  Batch-renames PDF files based on the "NAME:" field found inside each PDF.
  The renamed copies are saved to an output folder you choose.

FILES IN THIS PACKAGE
  pdf_renamer_gui.py   - Source code (Python)
  pdf_renamer.spec     - PyInstaller build spec
  requirements.txt     - Python dependencies
  build_windows.bat    - One-click build script
  installer.iss        - Inno Setup script (optional installer)


HOW TO BUILD THE EXE (Windows only)
------------------------------------
REQUIREMENTS: Python 3.9+ installed on a Windows PC
  - Download from https://python.org/downloads/
  - During install, tick "Add Python to PATH"

STEPS:
  1. Copy this entire folder to a Windows machine
  2. Double-click  build_windows.bat
  3. Wait 1-3 minutes for the build to complete
  4. Find  dist\PDF Renamer.exe  — this is the standalone exe

The .exe is fully self-contained (~30-60 MB). Copy it to any Windows PC
and run it — no Python or any other software required.


OPTIONAL: CREATE A WINDOWS INSTALLER
--------------------------------------
  1. Download and install Inno Setup from https://jrsoftware.org/isdl.php
  2. Open installer.iss in Inno Setup
  3. Click Build > Compile
  4. Find the installer in  installer_output\PDFRenamer_Setup_v1.0.exe


USAGE (GUI)
-----------
  1. Run  PDF Renamer.exe
  2. Click "Browse…" next to Source folder — select folder with PDFs to rename
  3. Click "Browse…" next to Output folder — select where to save renamed files
  4. Click "▶ Start Renaming"
  5. Watch the log — green = renamed, yellow = skipped, red = error
  6. Renamed files appear in your output folder

NAME FIELD DETECTION
  The tool finds patterns like:
    NAME: John Doe
    Name: Jane Smith
    NAME - Robert Brown

  If a name contains "UAN NO", everything from that point is stripped.


ALTERNATIVE: GITHUB ACTIONS (no Windows machine needed)
---------------------------------------------------------
  If you don't have a Windows machine, you can build using GitHub Actions:
  1. Create a GitHub repository and push this folder
  2. Create  .github/workflows/build.yml  with the content below
  3. Push to trigger the build — download the .exe from Actions > Artifacts

  .github/workflows/build.yml content:
  ─────────────────────────────────────
  name: Build Windows EXE
  on: [push, workflow_dispatch]
  jobs:
    build:
      runs-on: windows-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: { python-version: '3.11' }
        - run: pip install pdfplumber PyPDF2 pyinstaller
        - run: pyinstaller pdf_renamer.spec --clean --noconfirm
        - uses: actions/upload-artifact@v4
          with:
            name: PDF-Renamer-Windows
            path: "dist/PDF Renamer.exe"
  ─────────────────────────────────────
