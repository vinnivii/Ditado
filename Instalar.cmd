@echo off
setlocal
set "installScript=%~dp0Instalar.ps1"
if not exist "%~dp0aplicativo\pacote.json" if exist "%~dp0distribuicao\WhisperDitado-2.0.0\Instalar.ps1" set "installScript=%~dp0distribuicao\WhisperDitado-2.0.0\Instalar.ps1"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%installScript%" %*
set "installResult=%ERRORLEVEL%"
if not "%installResult%"=="0" (
    echo.
    echo A instalacao nao foi concluida. Confira a mensagem acima.
)
exit /b %installResult%
