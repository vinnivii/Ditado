[CmdletBinding()]
param(
    [string]$Destino = (Join-Path $env:LOCALAPPDATA 'Programs\WhisperDitado'),
    [switch]$SemInicializacao,
    [switch]$SemIniciar,
    [switch]$SemAtalhos
)
$ErrorActionPreference = 'Stop'

function Assert-ChildPath([string]$Path, [string]$Parent) {
    $absolutePath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $absoluteParent = [IO.Path]::GetFullPath($Parent).TrimEnd('\')
    if (-not $absolutePath.StartsWith($absoluteParent + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Caminho fora do diretorio esperado: $absolutePath"
    }
    return $absolutePath
}

try {
    if (-not [Environment]::Is64BitOperatingSystem) { throw 'Este pacote requer Windows de 64 bits.' }
    $payload = Join-Path $PSScriptRoot 'aplicativo'
    if (-not (Test-Path -LiteralPath (Join-Path $payload 'pacote.json'))) {
        throw 'Pacote incompleto. Execute Instalar.cmd da pasta distribuicao\WhisperDitado-2.0.0, junto da pasta aplicativo.'
    }
    $target = [IO.Path]::GetFullPath($Destino).TrimEnd('\')
    $parentDir = Split-Path -Parent $target
    if (-not $parentDir -or $target -eq [IO.Path]::GetPathRoot($target).TrimEnd('\')) { throw 'Escolha uma pasta especifica para o aplicativo.' }
    if ((Test-Path -LiteralPath $target) -and -not (Test-Path -LiteralPath (Join-Path $target 'pacote.json'))) {
        throw "A pasta $target ja existe e nao pertence a esta instalacao. Escolha outro -Destino."
    }
    $scriptPath = Join-Path $target 'transcritor.py'
    $running = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" | Where-Object {
        $_.CommandLine -and $_.CommandLine.IndexOf($scriptPath, [StringComparison]::OrdinalIgnoreCase) -ge 0
    })
    if ($running.Count -gt 0) { throw 'O Whisper desta instalacao esta aberto. Use Sair no icone perto do relogio e execute novamente.' }
    New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    $stage = Assert-ChildPath ($target + '.stage-' + [Guid]::NewGuid().ToString('N')) $parentDir
    Write-Host 'Copiando o Whisper e os modelos. Nao e necessario baixar nada da internet...'
    & "$env:SystemRoot\System32\robocopy.exe" $payload $stage /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "Falha ao copiar o pacote (robocopy $LASTEXITCODE)." }
    $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $stage 'pacote.json') | ConvertFrom-Json
    foreach ($entry in $manifest.arquivos) {
        $filePath = Assert-ChildPath (Join-Path $stage $entry.caminho) $stage
        if (-not (Test-Path -LiteralPath $filePath)) { throw "Arquivo ausente: $($entry.caminho)" }
        if ((Get-FileHash -Algorithm SHA256 -LiteralPath $filePath).Hash -ne $entry.sha256) {
            throw "Arquivo danificado: $($entry.caminho). Copie novamente o pacote."
        }
    }
    Write-Host 'Verificando Python, transcricao e audio...'
    & (Join-Path $stage 'runtime\python.exe') -X utf8 (Join-Path $stage 'diagnostico.py')
    if ($LASTEXITCODE -ne 0) { throw 'A verificacao falhou. A instalacao anterior foi preservada.' }
    $backup = $null
    if (Test-Path -LiteralPath $target) {
        $backup = Assert-ChildPath ($target + '.backup-' + [Guid]::NewGuid().ToString('N')) $parentDir
        $verifiedOld = Assert-ChildPath $target $parentDir
        Move-Item -LiteralPath $verifiedOld -Destination $backup
    }
    try {
        $verifiedStage = Assert-ChildPath $stage $parentDir
        $verifiedTarget = Assert-ChildPath $target $parentDir
        Move-Item -LiteralPath $verifiedStage -Destination $verifiedTarget
    } catch {
        if ($backup -and (Test-Path -LiteralPath $backup)) {
            $verifiedRestore = Assert-ChildPath $backup $parentDir
            Move-Item -LiteralPath $verifiedRestore -Destination $target
        }
        throw
    }
    $pythonw = Join-Path $target 'runtime\pythonw.exe'
    $arguments = '-X utf8 "' + (Join-Path $target 'transcritor.py') + '"'
    $shellLink = New-Object -ComObject WScript.Shell
    function Add-Shortcut([string]$Folder, [bool]$Background) {
        New-Item -ItemType Directory -Path $Folder -Force | Out-Null
        $link = $shellLink.CreateShortcut((Join-Path $Folder 'Whisper - Ditado de ocorrencias.lnk'))
        $link.TargetPath = $pythonw
        $link.Arguments = $arguments
        if ($Background) { $link.Arguments += ' --background' }
        $link.WorkingDirectory = $target
        $link.Description = 'Ctrl+Alt+Espaco para gravar e parar. Ctrl+V para colar.'
        $link.IconLocation = (Join-Path $target 'whisper.ico') + ',0'
        $link.Save()
    }
    if (-not $SemAtalhos) {
        Add-Shortcut ([Environment]::GetFolderPath('Desktop')) $false
        Add-Shortcut (Join-Path ([Environment]::GetFolderPath('Programs')) 'Whisper') $false
    }
    $startupLink = Join-Path ([Environment]::GetFolderPath('Startup')) 'Whisper - Ditado de ocorrencias.lnk'
    if (-not $SemInicializacao) { Add-Shortcut ([Environment]::GetFolderPath('Startup')) $true }
    elseif (Test-Path -LiteralPath $startupLink) {
        $existing = $shellLink.CreateShortcut($startupLink)
        if ($existing.TargetPath -eq $pythonw) { Remove-Item -LiteralPath $startupLink }
    }
    if ($backup) {
        $verifiedBackup = Assert-ChildPath $backup $parentDir
        Remove-Item -LiteralPath $verifiedBackup -Recurse -Force
    }
    Write-Host ('Instalado em: ' + $target)
    Write-Host 'Ctrl+Alt+Espaco: iniciar/parar. Aguarde o sinal e cole com Ctrl+V.'
    if (-not $SemIniciar) {
        Start-Process -FilePath $pythonw -ArgumentList ($arguments + ' --background') -WorkingDirectory $target -WindowStyle Hidden | Out-Null
    }
    exit 0
} catch {
    Write-Host ('ERRO: ' + $_.Exception.Message) -ForegroundColor Red
    if ($stage -and (Test-Path -LiteralPath $stage)) {
        $verifiedCleanup = Assert-ChildPath $stage $parentDir
        Remove-Item -LiteralPath $verifiedCleanup -Recurse -Force
    }
    exit 1
}
