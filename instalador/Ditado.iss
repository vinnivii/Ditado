#ifndef AppVersion
  #define AppVersion "2.1.0"
#endif

[Setup]
AppId={{2CE819B4-DA65-4668-AC70-47DE17CB5071}
AppName=Ditado
AppVersion={#AppVersion}
AppVerName=Ditado {#AppVersion}
AppPublisher=vinnivii
AppPublisherURL=https://github.com/vinnivii/Ditado
AppSupportURL=https://github.com/vinnivii/Ditado/issues
AppUpdatesURL=https://github.com/vinnivii/Ditado/releases
DefaultDirName={localappdata}\Programs\WhisperDitado
DefaultGroupName=Whisper
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#OutputDir}
OutputBaseFilename=Ditado-Setup-{#AppVersion}
SetupIconFile={#PayloadDir}\whisper.ico
UninstallDisplayIcon={app}\whisper.ico
UninstallDisplayName=Ditado
Uninstallable=yes
UninstallLogMode=append
WizardStyle=modern
Compression=lzma2/fast
SolidCompression=yes
LZMAUseSeparateProcess=yes
CloseApplications=no
RestartApplications=no
SetupMutex=Local\DitadoSetup
DisableStartupPrompt=yes
ChangesAssociations=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"
Name: "menuicon"; Description: "Criar atalhos no Menu Iniciar"; GroupDescription: "Atalhos:"
Name: "startup"; Description: "Iniciar o Ditado ao entrar no Windows"; GroupDescription: "Inicialização:"

[Files]
Source: "{#ProjectDir}\instalador\verificar_em_uso.ps1"; Flags: dontcopy
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Excludes: "pacote.json,LEIA-ME.txt,LICENCAS.txt,Abrir.cmd,__pycache__,*.pyc"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MetadataDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Whisper - Ditado de ocorrencias"; Filename: "{app}\runtime\pythonw.exe"; Parameters: "-B -X utf8 ""{app}\transcritor.py"""; WorkingDir: "{app}"; IconFilename: "{app}\whisper.ico"; Tasks: menuicon
Name: "{group}\Desinstalar Ditado"; Filename: "{uninstallexe}"; WorkingDir: "{app}"; IconFilename: "{app}\whisper.ico"; Tasks: menuicon
Name: "{userdesktop}\Whisper - Ditado de ocorrencias"; Filename: "{app}\runtime\pythonw.exe"; Parameters: "-B -X utf8 ""{app}\transcritor.py"""; WorkingDir: "{app}"; IconFilename: "{app}\whisper.ico"; Tasks: desktopicon
Name: "{userstartup}\Whisper - Ditado de ocorrencias"; Filename: "{app}\runtime\pythonw.exe"; Parameters: "-B -X utf8 ""{app}\transcritor.py"" --background"; WorkingDir: "{app}"; IconFilename: "{app}\whisper.ico"; Tasks: startup

[Run]
Filename: "{app}\runtime\pythonw.exe"; Parameters: "-B -X utf8 ""{app}\transcritor.py"" --background"; WorkingDir: "{app}"; Description: "Iniciar o Ditado agora"; Flags: nowait postinstall skipifsilent; Check: StartAfterSetup

[UninstallRun]
Filename: "{app}\runtime\python.exe"; Parameters: "-B -X utf8 ""{app}\instalacao\limpar_cache.py"""; WorkingDir: "{app}"; Flags: runhidden waituntilterminated skipifdoesntexist

[Code]
function StartAfterSetup: Boolean;
var
  I: Integer;
begin
  Result := True;
  for I := 1 to ParamCount do
    if CompareText(ParamStr(I), '/SEM_INICIAR') = 0 then
      Result := False;
end;

function CheckInstallation(const Script, Action: String): Integer;
var
  Code: Integer;
  Arguments: String;
begin
  Arguments := '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + Script +
    '" -Destino "' + ExpandConstant('{app}') + '" -Acao ' + Action;
  if Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
    Arguments, '', SW_HIDE, ewWaitUntilTerminated, Code) then
    Result := Code
  else
    Result := 20;
end;

function GuardError(Code: Integer): String;
begin
  case Code of
    0: Result := '';
    10: Result := 'O Ditado desta instalação está aberto. Clique com o botão direito no ícone perto do relógio, escolha Sair e tente novamente.';
    30: Result := 'Escolha uma pasta exclusiva para o Ditado. A pasta selecionada contém outros arquivos ou não pode ser usada.';
  else
    Result := 'Não foi possível verificar se o Ditado está em uso. Feche o programa e tente novamente.';
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  ExtractTemporaryFile('verificar_em_uso.ps1');
  Result := GuardError(CheckInstallation(ExpandConstant('{tmp}\verificar_em_uso.ps1'), 'Instalar'));
end;

procedure RemoveOwnedShortcut(const Path: String);
var
  Shell, Shortcut: Variant;
begin
  if not FileExists(Path) then Exit;
  try
    Shell := CreateOleObject('WScript.Shell');
    Shortcut := Shell.CreateShortcut(Path);
    if (CompareText(Shortcut.TargetPath, ExpandConstant('{app}\runtime\pythonw.exe')) = 0) or
      (CompareText(Shortcut.TargetPath, ExpandConstant('{uninstallexe}')) = 0) then
      DeleteFile(Path);
  except
    Log('Não foi possível atualizar o atalho: ' + Path);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Code: Integer;
begin
  if CurStep = ssPostInstall then begin
    if not Exec(ExpandConstant('{app}\runtime\python.exe'),
      '-B -X utf8 "' + ExpandConstant('{app}\diagnostico.py') + '"',
      ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, Code) then
      RaiseException('Não foi possível verificar o ambiente de transcrição.');
    if Code <> 0 then
      RaiseException('A verificação do ambiente falhou. Reinstale o Ditado.');
    if not WizardIsTaskSelected('startup') then
      RemoveOwnedShortcut(ExpandConstant('{userstartup}\Whisper - Ditado de ocorrencias.lnk'));
    if not WizardIsTaskSelected('desktopicon') then
      RemoveOwnedShortcut(ExpandConstant('{userdesktop}\Whisper - Ditado de ocorrencias.lnk'));
    if not WizardIsTaskSelected('menuicon') then begin
      RemoveOwnedShortcut(ExpandConstant('{group}\Whisper - Ditado de ocorrencias.lnk'));
      RemoveOwnedShortcut(ExpandConstant('{group}\Desinstalar Ditado.lnk'));
    end;
  end;
end;

function InitializeUninstall: Boolean;
var
  Script, Error: String;
begin
  Script := ExpandConstant('{app}\instalacao\verificar_em_uso.ps1');
  Result := True;
  if FileExists(Script) then begin
    Error := GuardError(CheckInstallation(Script, 'Desinstalar'));
    Result := Error = '';
    if not Result then
      SuppressibleMsgBox(Error, mbError, MB_OK, IDOK);
  end;
end;
