[CmdletBinding()]
param([switch]$Silencioso)
$ErrorActionPreference = 'Stop'
try {
    $key = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{2CE819B4-DA65-4668-AC70-47DE17CB5071}_is1'
    $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::CurrentUser, [Microsoft.Win32.RegistryView]::Registry64)
    $entry = $base.OpenSubKey($key)
    if (-not $entry) { throw 'Instalacao registrada do Ditado nao encontrada. Instale a versao 2.1.0 ou posterior.' }
    $location = $entry.GetValue('InstallLocation')
    $entry.Close()
    $base.Close()
    $uninstaller = Join-Path $location 'unins000.exe'
    if (-not (Test-Path -LiteralPath $uninstaller)) { throw 'Desinstalador nao encontrado. Reinstale o Ditado para reparar a instalacao.' }
    $uninstallArgs = '/NORESTART'
    if ($Silencioso) { $uninstallArgs += ' /VERYSILENT /SUPPRESSMSGBOXES' }
    $style = if ($Silencioso) { 'Hidden' } else { 'Normal' }
    $process = Start-Process -FilePath $uninstaller -ArgumentList $uninstallArgs -Wait -PassThru -WindowStyle $style
    exit $process.ExitCode
} catch {
    Write-Host ('ERRO: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
