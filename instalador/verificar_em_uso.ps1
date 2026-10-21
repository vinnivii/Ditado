param(
    [Parameter(Mandatory=$true)][string]$Destino,
    [ValidateSet('Instalar','Desinstalar')][string]$Acao = 'Instalar'
)
$ErrorActionPreference = 'Stop'
try {
    $target = [IO.Path]::GetFullPath($Destino).TrimEnd('\')
    $blocked = @([IO.Path]::GetPathRoot($target).TrimEnd('\'), $env:USERPROFILE, $env:LOCALAPPDATA,
        $env:APPDATA, $env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:SystemRoot,
        [Environment]::GetFolderPath('Desktop'), (Join-Path $env:LOCALAPPDATA 'Programs'))
    foreach ($folder in $blocked) {
        if ($folder -and $target -eq [IO.Path]::GetFullPath($folder).TrimEnd('\')) { exit 30 }
    }
    if (Test-Path -LiteralPath $target) {
        $item = Get-Item -LiteralPath $target
        if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { exit 30 }
        if ($Acao -eq 'Instalar') {
            $contents = @(Get-ChildItem -LiteralPath $target -Force)
            if ($contents.Count -gt 0) {
                if (-not (Test-Path -LiteralPath (Join-Path $target 'pacote.json')) -or
                    -not (Test-Path -LiteralPath (Join-Path $target 'transcritor.py')) -or
                    -not (Test-Path -LiteralPath (Join-Path $target 'runtime\pythonw.exe'))) { exit 30 }
                $marker = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $target 'pacote.json') | ConvertFrom-Json
                if (-not $marker.versao -or -not $marker.arquivos) { exit 30 }
            }
        }
    }
    $scriptPath = Join-Path $target 'transcritor.py'
    $running = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" | Where-Object {
        $_.CommandLine -and $_.CommandLine.IndexOf($scriptPath, [StringComparison]::OrdinalIgnoreCase) -ge 0
    })
    if ($running.Count -gt 0) { exit 10 }
    exit 0
} catch {
    exit 20
}
