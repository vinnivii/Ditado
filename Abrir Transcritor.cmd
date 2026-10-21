@echo off
if exist "%LOCALAPPDATA%\Programs\WhisperDitado\runtime\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\WhisperDitado\runtime\pythonw.exe" -X utf8 "%LOCALAPPDATA%\Programs\WhisperDitado\transcritor.py"
    exit /b 0
)
cd /d "%~dp0"
if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo Python do transcritor nao encontrado nesta pasta.
    pause
    exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" -X utf8 "%~dp0transcritor.py"
