@echo off
setlocal

REM One-click build helper for Windows (run from project root)
REM Creates venv (if missing), installs requirements, and builds a single exe with PyInstaller

if not exist venv\Scripts\python.exe (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt

echo Building with PyInstaller (onefile, windowed)...
pyinstaller --noconfirm --clean --onefile --windowed --name Phonotify --add-data "icons;icons" src\main.py

if %ERRORLEVEL% neq 0 (
    echo PyInstaller failed with exit code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo Build complete. See dist\Phonotify.exe
pause
