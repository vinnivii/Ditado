$ErrorActionPreference = 'Stop'
try {
    $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{2CE819B4-DA65-4668-AC70-47DE17CB5071}_is1'
    $entry = Get-ItemProperty -LiteralPath $key -ErrorAction SilentlyContinue
    $candidates = @()
    if ($entry) { $candidates += $entry.InstallLocation }
    $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Ditado')
    foreach ($folder in $candidates) {
        $python = Join-Path $folder 'runtime\pythonw.exe'
        $script = Join-Path $folder 'transcritor.py'
        if ((Test-Path -LiteralPath $python) -and (Test-Path -LiteralPath $script)) {
            Start-Process -FilePath $python -ArgumentList ('-B -X utf8 "' + $script + '"') -WorkingDirectory $folder -WindowStyle Hidden
            exit 0
        }
    }
    $python = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'Instale o Ditado antes de abrir o aplicativo.' }
    Start-Process -FilePath $python -ArgumentList ('-B -X utf8 "' + (Join-Path $PSScriptRoot 'transcritor.py') + '"') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
} catch {
    Write-Host ('ERRO: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
