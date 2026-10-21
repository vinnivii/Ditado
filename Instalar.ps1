[CmdletBinding()]
param(
    [string]$Destino,
    [switch]$SemInicializacao,
    [switch]$SemIniciar,
    [switch]$SemAtalhos,
    [switch]$Silencioso,
    [string]$Log
)
$ErrorActionPreference = 'Stop'
try {
    $version = (Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'VERSAO.txt')).Trim()
    $fileName = "Ditado-Setup-$version.exe"
    $candidates = @((Join-Path $PSScriptRoot $fileName), (Join-Path $PSScriptRoot ("distribuicao\" + $fileName)))
    $installer = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $installer) { throw "Baixe $fileName em https://github.com/vinnivii/Ditado/releases e coloque-o nesta pasta ou em distribuicao." }
    $installArgs = @('/NORESTART')
    if ($Silencioso) { $installArgs += @('/VERYSILENT','/SUPPRESSMSGBOXES') }
    if ($SemIniciar) { $installArgs += '/SEM_INICIAR' }
    if ($Destino) { $installArgs += '/DIR="' + $Destino + '"' }
    if ($Log) { $installArgs += '/LOG="' + $Log + '"' }
    $disabledTasks = @()
    if ($SemInicializacao) { $disabledTasks += '!startup' }
    if ($SemAtalhos) { $disabledTasks += @('!desktopicon','!menuicon') }
    if ($disabledTasks.Count) { $installArgs += '/MERGETASKS="' + ($disabledTasks -join ',') + '"' }
    $style = if ($Silencioso) { 'Hidden' } else { 'Normal' }
    $process = Start-Process -FilePath $installer -ArgumentList ($installArgs -join ' ') -Wait -PassThru -WindowStyle $style
    exit $process.ExitCode
} catch {
    Write-Host ('ERRO: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
