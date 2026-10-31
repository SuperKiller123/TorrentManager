#define MyAppName "Torrent Manager"
#define MyAppVersion "0.8"
[Setup]
#ifdef TM_TEST_ROOT
AppId={{D186A29D-D24B-4A19-81C6-7EFD2330B872}
DefaultDirName={#TM_TEST_ROOT}\Torrent Manager
PrivilegesRequired=lowest
#else
AppId={{4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F}
DefaultDirName={autopf}\Torrent Manager
PrivilegesRequired=admin
#endif
AppName={#MyAppName}
AppVerName={#MyAppName}
AppVersion={#MyAppVersion}
UninstallDisplayName={#MyAppName}
DefaultGroupName=Torrent Manager
OutputDir=dist\installer
OutputBaseFilename=TorrentManager-Setup-v0.8
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\TorrentManager.exe
SetupIconFile=assets\app_icon.ico
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
UsePreviousGroup=yes
UsePreviousTasks=yes
UsePreviousLanguage=yes
ShowLanguageDialog=yes
LanguageDetectionMethod=none
UninstallLogging=yes

; All Setup text is consistently English, as explicitly accepted.
[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "zh"; MessagesFile: "compiler:Default.isl"
Name: "hi"; MessagesFile: "compiler:Default.isl"
Name: "es"; MessagesFile: "compiler:Default.isl"
Name: "fr"; MessagesFile: "compiler:Default.isl"
Name: "ar"; MessagesFile: "compiler:Default.isl"
Name: "bn"; MessagesFile: "compiler:Default.isl"
Name: "pt"; MessagesFile: "compiler:Default.isl"
Name: "ru"; MessagesFile: "compiler:Default.isl"
Name: "ur"; MessagesFile: "compiler:Default.isl"
Name: "hu"; MessagesFile: "compiler:Default.isl"
Name: "de"; MessagesFile: "compiler:Default.isl"
[LangOptions]
en.LanguageName=English
zh.LanguageName=中文（简体）
hi.LanguageName=हिन्दी
es.LanguageName=Español
fr.LanguageName=Français
ar.LanguageName=العربية
bn.LanguageName=বাংলা
pt.LanguageName=Português
ru.LanguageName=Русский
ur.LanguageName=اردو
hu.LanguageName=Magyar
de.LanguageName=Deutsch
[Messages]
SelectLanguageLabel=Select the language for Torrent Manager.
; Inno's administrative-install marker is independent of the install location.
UninstallDisplayNameMark=%1
UninstallDisplayNameMarks=%1
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Options:"; Flags: unchecked
Name: "startup"; Description: "Start Torrent Manager with Windows"; GroupDescription: "Options:"; Flags: unchecked
Name: "close_to_tray"; Description: "Keep running in the notification area when closing the window"; GroupDescription: "Options:"; Flags: unchecked
Name: "pin_taskbar"; Description: "Pin to taskbar (instructions)"; GroupDescription: "Options:"; Flags: unchecked
Name: "pin_start"; Description: "Pin to Start (instructions)"; GroupDescription: "Options:"; Flags: unchecked
[Files]
#ifdef TM_TEST_SOURCE
Source: "{#TM_TEST_SOURCE}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#else
Source: "dist\TorrentManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif
Source: "uninstall_cleanup.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "pinning-help.html"; DestDir: "{app}"; Flags: ignoreversion
#ifndef TM_TEST_ROOT
[Icons]
Name: "{autoprograms}\Torrent Manager"; Filename: "{app}\TorrentManager.exe"
#endif
[INI]
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "language"; String: "{language}"
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "desktopicon"; String: "{code:DesktopValue}"
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "startup"; String: "{code:StartupValue}"
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "close_to_tray"; String: "{code:TrayValue}"
[Run]
#ifndef TM_TEST_ROOT
Filename: "{app}\TorrentManager.exe"; Description: "Launch Torrent Manager"; Flags: nowait postinstall skipifsilent runasoriginaluser
Filename: "{app}\pinning-help.html"; Description: "Open pinning instructions"; Tasks: pin_taskbar or pin_start; Flags: shellexec nowait postinstall skipifsilent runasoriginaluser
#endif
[UninstallDelete]
Type: files; Name: "{app}\install-defaults.ini"
Type: dirifempty; Name: "{app}"
[Code]
var
  CleanupScript, CleanupReport: String;
  CleanupAvailable: Boolean;

function DesktopValue(Param: String): String;
begin
  if WizardIsTaskSelected('desktopicon') then Result := 'true' else Result := 'false';
end;
function StartupValue(Param: String): String;
begin
  if WizardIsTaskSelected('startup') then Result := 'true' else Result := 'false';
end;
function TrayValue(Param: String): String;
begin
  if WizardIsTaskSelected('close_to_tray') then Result := 'true' else Result := 'false';
end;
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (GetPreviousData('Installed', '') = 'yes') and
    ((PageID = wpSelectDir) or (PageID = wpSelectProgramGroup));
end;
procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  SetPreviousData(PreviousDataKey, 'Installed', 'yes');
end;
function ValidInstallDirectory(Directory: String): Boolean;
begin
  Result := (CompareText(ExtractFileName(RemoveBackslashUnlessRoot(Directory)), 'Torrent Manager') = 0);
#ifdef TM_TEST_ROOT
  Result := Result and (CompareText(Directory, '{#TM_TEST_ROOT}\Torrent Manager') = 0);
#endif
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = wpSelectDir) and not ValidInstallDirectory(WizardDirValue) then begin
    MsgBox('Choose a dedicated folder named Torrent Manager. This keeps application removal separate from your other files.', mbError, MB_OK);
    Result := False;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if not ValidInstallDirectory(ExpandConstant('{app}')) then
    Result := 'Installation requires a dedicated folder named Torrent Manager.';
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    if not SaveStringToFile(ExpandConstant('{app}\.torrentmanager-install'), '4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F', False) then
      RaiseException('Cannot write the application ownership marker.');
end;

function RunCleanup(Mode: String): Boolean;
var
  ExitCode: Integer;
  Args: String;
begin
  Args := '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + CleanupScript +
    '" -Mode ' + Mode + ' -AppDirectory "' + ExpandConstant('{app}') + '" -ReportPath "' + CleanupReport + '"';
#ifdef TM_TEST_ROOT
  Args := Args + ' -TestRoot "{#TM_TEST_ROOT}"';
#endif
  Result := Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'), Args, '', SW_HIDE, ewWaitUntilTerminated, ExitCode) and (ExitCode = 0);
end;

function InitializeUninstall: Boolean;
begin
  CleanupScript := ExpandConstant('{tmp}\TorrentManager-uninstall.ps1');
  CleanupReport := ExpandConstant('{tmp}\TorrentManager-uninstall-report.txt');
  CleanupAvailable := FileCopy(ExpandConstant('{app}\uninstall_cleanup.ps1'), CleanupScript, False);
  Result := CleanupAvailable;
  if not Result then
    MsgBox('The cleanup helper is missing. Reinstall Torrent Manager v0.8, then uninstall it again.', mbError, MB_OK);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then begin
    if not RunCleanup('Prepare') then
      RaiseException('Torrent Manager could not close its processes safely. See ' + CleanupReport);
  end;
  if (CurUninstallStep = usPostUninstall) and CleanupAvailable then begin
    if not RunCleanup('Remove') then begin
      Log('Some application data could not be removed. Report: ' + CleanupReport);
      if not UninstallSilent then
        MsgBox('Some files were preserved or could not be removed. Torrent downloads were not deleted. Details: ' + CleanupReport, mbError, MB_OK);
    end;
  end;
end;
