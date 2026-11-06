#define MyAppName "Torrent Manager"
#define MyAppVersion "1.0"
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
OutputBaseFilename=TorrentManager-Setup-v1.0
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
DisableReadyPage=yes
DisableFinishedPage=yes

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "zh"; MessagesFile: "installer-languages\ChineseSimplified.isl"
Name: "hi"; MessagesFile: "installer-languages\Hindi.islu"
Name: "es"; MessagesFile: "installer-languages\Spanish.isl"
Name: "fr"; MessagesFile: "installer-languages\French.isl"
Name: "ar"; MessagesFile: "installer-languages\Arabic.isl"
Name: "bn"; MessagesFile: "installer-languages\Bengali.islu"
Name: "pt"; MessagesFile: "installer-languages\Portuguese.isl"
Name: "ru"; MessagesFile: "installer-languages\Russian.isl"
Name: "ur"; MessagesFile: "installer-languages\Urdu.isl"
Name: "hu"; MessagesFile: "installer-languages\Hungarian.isl"
Name: "de"; MessagesFile: "installer-languages\German.isl"
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
Name: "startup"; Description: "{cm:StartupTask}"; Flags: unchecked
Name: "close_to_tray"; Description: "{cm:TrayTask}"; Flags: unchecked
Name: "minimize_to_tray"; Description: "{cm:MinimizeTrayTask}"; Flags: unchecked

[CustomMessages]
hu.StartupTask=Indítás a Windowszal
hu.TrayTask=Bezáráskor futás az értesítési területen
hu.MinimizeTrayTask=Tálcára helyezéskor futtatás az értesítési területen
en.StartupTask=Start with Windows
en.TrayTask=Close window to notification area
en.MinimizeTrayTask=Run in notification area when minimized
de.StartupTask=Mit Windows starten
de.TrayTask=Beim Schließen im Infobereich weiterlaufen
de.MinimizeTrayTask=Beim Minimieren im Infobereich weiterlaufen
zh.StartupTask=随 Windows 启动
zh.TrayTask=关闭窗口后在通知区域继续运行
zh.MinimizeTrayTask=最小化时在通知区域运行
hi.StartupTask=Windows के साथ शुरू करें
hi.TrayTask=विंडो बंद करने पर सूचना क्षेत्र में चलते रहें
hi.MinimizeTrayTask=छोटा करने पर सूचना क्षेत्र में चलाएँ
es.StartupTask=Iniciar con Windows
es.TrayTask=Seguir en el área de notificación al cerrar
es.MinimizeTrayTask=Ejecutar en el área de notificación al minimizar
fr.StartupTask=Démarrer avec Windows
fr.TrayTask=Rester dans la zone de notification à la fermeture
fr.MinimizeTrayTask=Exécuter dans la zone de notification si réduit
ar.StartupTask=بدء التشغيل مع Windows
ar.TrayTask=الاستمرار في منطقة الإشعارات عند إغلاق النافذة
ar.MinimizeTrayTask=التشغيل في منطقة الإشعارات عند التصغير
bn.StartupTask=Windows-এর সাথে চালু করুন
bn.TrayTask=উইন্ডো বন্ধ করলে বিজ্ঞপ্তি এলাকায় চালু রাখুন
bn.MinimizeTrayTask=মিনিমাইজ করলে বিজ্ঞপ্তি এলাকায় চালান
pt.StartupTask=Iniciar com o Windows
pt.TrayTask=Continuar na área de notificação ao fechar
pt.MinimizeTrayTask=Executar na área de notificação ao minimizar
ru.StartupTask=Запускать с Windows
ru.TrayTask=При закрытии оставлять в области уведомлений
ru.MinimizeTrayTask=При сворачивании работать в области уведомлений
ur.StartupTask=Windows کے ساتھ شروع کریں
ur.TrayTask=ونڈو بند ہونے پر اطلاعاتی حصے میں چلتے رہیں
ur.MinimizeTrayTask=چھوٹا کرنے پر اطلاعاتی حصے میں چلائیں
[Files]
#ifdef TM_TEST_SOURCE
Source: "{#TM_TEST_SOURCE}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#else
Source: "dist\TorrentManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif
Source: "uninstall_cleanup.ps1"; DestDir: "{app}"; Flags: ignoreversion
#ifndef TM_TEST_ROOT
[Icons]
Name: "{autoprograms}\Torrent Manager"; Filename: "{app}\TorrentManager.exe"
#endif
[INI]
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "language"; String: "{language}"
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "startup"; String: "{code:StartupValue}"
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "close_to_tray"; String: "{code:TrayValue}"
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "minimize_to_tray"; String: "{code:MinimizeTrayValue}"
[Run]
#ifndef TM_TEST_ROOT
Filename: "{app}\TorrentManager.exe"; Description: "Launch Torrent Manager"; Flags: nowait skipifsilent runasoriginaluser
#endif
[UninstallDelete]
Type: files; Name: "{app}\install-defaults.ini"
Type: dirifempty; Name: "{app}"
[Code]
var
  CleanupScript, CleanupReport: String;
  CleanupAvailable: Boolean;

function StartupValue(Param: String): String;
begin
  if WizardIsTaskSelected('startup') then Result := 'true' else Result := 'false';
end;
function TrayValue(Param: String): String;
begin
  if WizardIsTaskSelected('close_to_tray') then Result := 'true' else Result := 'false';
end;
function MinimizeTrayValue(Param: String): String;
begin
  if WizardIsTaskSelected('minimize_to_tray') then Result := 'true' else Result := 'false';
end;
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpSelectTasks then
    WizardForm.NextButton.Caption := SetupMessage(msgButtonInstall);
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
var
  UninstallKey, UninstallCommand: String;
  RootKey: Integer;
begin
  if CurStep = ssPostInstall then begin
    if not SaveStringToFile(ExpandConstant('{app}\.torrentmanager-install'), '4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F', False) then
      RaiseException('Cannot write the application ownership marker.');
    if IsAdminInstallMode then begin
      RootKey := HKLM;
      UninstallKey := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F}_is1';
    end else begin
      RootKey := HKCU;
      UninstallKey := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{D186A29D-D24B-4A19-81C6-7EFD2330B872}_is1';
    end;
    UninstallCommand := '"' + ExpandConstant('{uninstallexe}') + '" /SILENT';
    if not RegWriteStringValue(RootKey, UninstallKey, 'UninstallString', UninstallCommand) then
      RaiseException('Cannot update the Windows uninstall command.');
  end;
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
    MsgBox('The cleanup helper is missing. Reinstall Torrent Manager v1.0, then uninstall it again.', mbError, MB_OK);
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
