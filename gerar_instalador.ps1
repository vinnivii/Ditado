[CmdletBinding()]
param([string]$OrigemAplicativo, [string]$Compilador)
$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$version = (Get-Content -Raw -LiteralPath (Join-Path $project 'VERSAO.txt')).Trim()
if (-not $OrigemAplicativo) {
    $OrigemAplicativo = Join-Path $project ("distribuicao\WhisperDitado-$version\aplicativo")
    if (-not (Test-Path -LiteralPath $OrigemAplicativo)) {
        $OrigemAplicativo = Join-Path $project 'distribuicao\WhisperDitado-2.0.0\aplicativo'
    }
}
$payload = [IO.Path]::GetFullPath($OrigemAplicativo)
if (-not (Test-Path -LiteralPath (Join-Path $payload 'pacote.json'))) { throw 'Prepare o pacote portátil com gerar_pacote.py antes de compilar.' }
if (-not $Compilador) {
    $candidates = @((Join-Path $env:ProgramFiles 'Inno Setup 7\ISCC.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 7\ISCC.exe'),
        (Join-Path $project 'verificacao\ferramentas\InnoSetup7\ISCC.exe'))
    $Compilador = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $Compilador) { throw 'Instale o Inno Setup 7 ou informe -Compilador com o caminho do ISCC.exe.' }
$compilerVersion = & $Compilador '--version'
if ($LASTEXITCODE -ne 0 -or ([version]$compilerVersion).Major -lt 7) { throw 'Use Inno Setup 7 para suportar caminhos longos das dependencias.' }
$python = Join-Path $project '.venv\Scripts\python.exe'
$output = Join-Path $project 'distribuicao'
$metadata = Join-Path $output ("metadados-$version")
& $python -B -X utf8 (Join-Path $project 'instalador\preparar_metadados.py') $payload $metadata $version
if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar os metadados.' }
& $Compilador '/Qp' "/DAppVersion=$version" "/DPayloadDir=$payload" "/DMetadataDir=$metadata" "/DProjectDir=$project" "/DOutputDir=$output" (Join-Path $project 'instalador\Ditado.iss')
if ($LASTEXITCODE -ne 0) { throw 'A compilacao do instalador falhou.' }
$installer = Join-Path $output ("Ditado-Setup-$version.exe")
$checksum = (Get-FileHash -Algorithm SHA256 -LiteralPath $installer).Hash.ToLowerInvariant()
$checksum + '  ' + [IO.Path]::GetFileName($installer) | Set-Content -LiteralPath ($installer + '.sha256') -Encoding ASCII
Write-Host ("Instalador: $installer")
