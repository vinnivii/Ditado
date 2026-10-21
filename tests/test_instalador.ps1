[CmdletBinding()]
param([string]$Instalador)
$ErrorActionPreference = 'Stop'
$project = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$version = (Get-Content -Raw -LiteralPath (Join-Path $project 'VERSAO.txt')).Trim()
if (-not $Instalador) { $Instalador = Join-Path $project ("distribuicao\Ditado-Setup-$version.exe") }
$uninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{2CE819B4-DA65-4668-AC70-47DE17CB5071}_is1'
if (Test-Path -LiteralPath $uninstallKey) { throw 'Ja existe uma instalacao registrada. Execute este teste em um perfil sem Ditado 2.1 instalado.' }
$sandbox = Join-Path $project ('verificacao\ciclo-instalador-' + [Guid]::NewGuid().ToString('N'))
$target = Join-Path $sandbox 'aplicativo'
$group = 'Whisper'
$groupDir = Join-Path ([Environment]::GetFolderPath('Programs')) $group
$desktopLink = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Whisper - Ditado de ocorrencias.lnk'
$startupLink = Join-Path ([Environment]::GetFolderPath('Startup')) 'Whisper - Ditado de ocorrencias.lnk'
$menuLink = Join-Path $groupDir 'Whisper - Ditado de ocorrencias.lnk'
$removeLink = Join-Path $groupDir 'Desinstalar Ditado.lnk'
$originalLinks = @{}
foreach ($path in @($desktopLink,$startupLink,$menuLink,$removeLink)) {
    if (Test-Path -LiteralPath $path) { $originalLinks[$path] = [IO.File]::ReadAllBytes($path) }
    else { $originalLinks[$path] = $null }
}
$settings = Join-Path $env:LOCALAPPDATA 'WhisperDitado\config.json'
$settingsHash = if (Test-Path -LiteralPath $settings) { (Get-FileHash -LiteralPath $settings).Hash } else { $null }
New-Item -ItemType Directory -Path $sandbox -Force | Out-Null
$shellLink = New-Object -ComObject WScript.Shell
$fakeProcess = $null
$success = $false

function Assert-True([bool]$Condition,[string]$Message) { if (-not $Condition) { throw $Message } }
function Run-Setup([string]$LogName,[string]$Tasks = '/TASKS="desktopicon,menuicon,startup"') {
    $arguments = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SEM_INICIAR /DIR="' + $target +
        '" /GROUP="' + $group + '" ' + $Tasks + ' /LOG="' + (Join-Path $sandbox $LogName) + '"'
    $process = Start-Process -FilePath $Instalador -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
    return $process.ExitCode
}

try {
    Write-Host '1/5 Instalando a copia de teste...'
    $installCode = Run-Setup 'instalacao.log'
    Assert-True ($installCode -eq 0) ("Falha na instalacao: $installCode")
    $entry = Get-ItemProperty -LiteralPath $uninstallKey
    Assert-True ($entry.DisplayName -eq 'Ditado' -and $entry.DisplayVersion -eq $version) 'Registro do Painel de Controle incorreto.'
    Assert-True ($entry.QuietUninstallString -like '*unins000.exe*') 'Desinstalacao silenciosa nao registrada.'
    Assert-True ($entry.InstallLocation.TrimEnd('\') -eq $target) 'O Registro aponta para outro destino.'
    $registeredCommand = $entry.UninstallString
    Assert-True ($registeredCommand -match '^"([^"]+)"') 'UninstallString invalido.'
    $uninstaller = $Matches[1]
    Assert-True ([IO.Path]::GetFullPath($uninstaller).StartsWith($target + '\',[StringComparison]::OrdinalIgnoreCase)) 'Desinstalador fora da copia de teste.'
    foreach ($path in @($desktopLink,$startupLink)) {
        Assert-True (Test-Path -LiteralPath $path) ("Atalho ausente: $path")
        $shortcut = $shellLink.CreateShortcut($path)
        Assert-True ($shortcut.TargetPath -eq (Join-Path $target 'runtime\pythonw.exe')) 'Atalho aponta para outra instalacao.'
    }
    Assert-True (Test-Path -LiteralPath (Join-Path $groupDir 'Desinstalar Ditado.lnk')) 'Atalho do desinstalador ausente.'
    $marker = Get-Content -Raw -LiteralPath (Join-Path $target 'pacote.json') | ConvertFrom-Json
    Assert-True ($marker.versao -eq $version -and $marker.produto -eq 'Ditado') 'Versao do payload incorreta.'

    Write-Host '2/5 Testando bloqueio de instalacao e remocao enquanto o programa esta em uso...'
    $fakeArgs = '-B -c "import time; time.sleep(120)" "' + (Join-Path $target 'transcritor.py') + '"'
    $fakeProcess = Start-Process -FilePath (Join-Path $target 'runtime\python.exe') -ArgumentList $fakeArgs -WindowStyle Hidden -PassThru
    $blockedInstallCode = Run-Setup 'instalacao-bloqueada.log'
    Assert-True ($blockedInstallCode -ne 0) 'A instalacao ignorou o processo em uso.'
    $blockedUninstall = Start-Process -FilePath $uninstaller -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -WindowStyle Hidden -Wait -PassThru
    Assert-True ($blockedUninstall.ExitCode -ne 0) 'A desinstalacao ignorou o processo em uso.'
    Assert-True (Test-Path -LiteralPath $uninstallKey) 'O bloqueio removeu o registro.'
    if (-not $fakeProcess.HasExited) { Stop-Process -Id $fakeProcess.Id -Force }
    $fakeProcess = $null

    $document = Join-Path $target 'minha-ocorrencia-teste.txt'
    'Texto do usuario que deve ser preservado.' | Set-Content -LiteralPath $document -Encoding UTF8
    $cache = Join-Path $target 'runtime\Lib\__pycache__'
    New-Item -ItemType Directory -Path $cache -Force | Out-Null
    [IO.File]::WriteAllBytes((Join-Path $cache 'teste.cpython-311.pyc'),[byte[]](1,2,3))

    Write-Host '3/5 Reinstalando para testar atualizacao sem duplicar a entrada...'
    $upgradeCode = Run-Setup 'atualizacao.log' '/TASKS="desktopicon,menuicon"'
    Assert-True ($upgradeCode -eq 0) ("Falha na atualizacao: $upgradeCode")
    Assert-True (-not (Test-Path -LiteralPath $startupLink)) 'A tarefa desmarcada manteve a inicializacao automatica.'
    Assert-True (Test-Path -LiteralPath $document) 'A atualizacao removeu um documento do usuario.'
    $sameEntries = @(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall' | Get-ItemProperty | Where-Object DisplayName -eq 'Ditado')
    Assert-True ($sameEntries.Count -eq 1) 'A atualizacao duplicou a entrada no Painel de Controle.'

    Write-Host '4/5 Removendo pelo comando registrado no Painel de Controle...'
    $uninstallArguments = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG="' + (Join-Path $sandbox 'desinstalacao.log') + '"'
    $uninstallProcess = Start-Process -FilePath $uninstaller -ArgumentList $uninstallArguments -WindowStyle Hidden -Wait -PassThru
    Assert-True ($uninstallProcess.ExitCode -eq 0) ("Falha ao desinstalar: $($uninstallProcess.ExitCode)")
    Assert-True (-not (Test-Path -LiteralPath $uninstallKey)) 'O registro de desinstalacao permaneceu.'
    Assert-True (-not (Test-Path -LiteralPath (Join-Path $target 'runtime\python.exe'))) 'O runtime permaneceu instalado.'
    Assert-True (-not (Test-Path -LiteralPath (Join-Path $target 'modelos\base.pt'))) 'Os modelos permaneceram instalados.'
    Assert-True (-not (Test-Path -LiteralPath $cache)) 'O cache nao foi limpo.'
    Assert-True (-not (Test-Path -LiteralPath $desktopLink)) 'O atalho da Area de Trabalho permaneceu.'
    Assert-True (-not (Test-Path -LiteralPath $menuLink)) 'O atalho do Menu Iniciar permaneceu.'
    Assert-True (-not (Test-Path -LiteralPath $removeLink)) 'O atalho do desinstalador permaneceu.'
    Assert-True (Test-Path -LiteralPath $document) 'A desinstalacao removeu um documento do usuario.'
    if ($settingsHash) { Assert-True ((Get-FileHash -LiteralPath $settings).Hash -eq $settingsHash) 'As preferencias foram alteradas.' }
    $report = @{ sucesso=$true; versao=$version; instalacao=$installCode; atualizacao=$upgradeCode;
        desinstalacao=$uninstallProcess.ExitCode; painel_de_controle=$registeredCommand;
        bloqueio_instalacao=$blockedInstallCode; bloqueio_desinstalacao=$blockedUninstall.ExitCode;
        documentos_preservados=$true; preferencias_preservadas=$true; atalhos_removidos=$true }
    $report | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $project 'verificacao\ciclo-instalador-2.1.0.json') -Encoding UTF8
    $success = $true
    Write-Host '5/5 Ciclo de instalacao, atualizacao e desinstalacao validado.'
} finally {
    if ($fakeProcess -and -not $fakeProcess.HasExited) { Stop-Process -Id $fakeProcess.Id -Force }
    if (-not $success -and (Test-Path -LiteralPath $uninstallKey)) {
        $remaining = Get-ItemProperty -LiteralPath $uninstallKey
        $ownedPath = [IO.Path]::GetFullPath($remaining.InstallLocation).TrimEnd('\')
        $allowedPath = [IO.Path]::GetFullPath($target).TrimEnd('\')
        if ($ownedPath -eq $allowedPath -and $ownedPath.StartsWith($project + '\verificacao\',[StringComparison]::OrdinalIgnoreCase)) {
            $ownedUninstaller = Join-Path $ownedPath 'unins000.exe'
            if (Test-Path -LiteralPath $ownedUninstaller) {
                Start-Process -FilePath $ownedUninstaller -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -WindowStyle Hidden -Wait | Out-Null
            }
        }
    }
    foreach ($path in $originalLinks.Keys) {
        if ($null -ne $originalLinks[$path]) {
            New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force | Out-Null
            [IO.File]::WriteAllBytes($path,$originalLinks[$path])
        }
    }
    if ($success) {
        $absoluteTarget = [IO.Path]::GetFullPath($target)
        $absoluteSandbox = [IO.Path]::GetFullPath($sandbox)
        Assert-True ($absoluteTarget.StartsWith($absoluteSandbox + '\',[StringComparison]::OrdinalIgnoreCase)) 'Limpeza fora da copia de teste.'
        Assert-True ($absoluteSandbox.StartsWith($project + '\verificacao\',[StringComparison]::OrdinalIgnoreCase)) 'Sandbox fora do workspace.'
        Remove-Item -LiteralPath $absoluteTarget -Recurse -Force
    }
}
