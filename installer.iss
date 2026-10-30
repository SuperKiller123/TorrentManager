#define MyAppName "Torrent Manager"
#define MyAppVersion "0.7"
[Setup]
AppId={{4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F}
AppName={#MyAppName}
AppVerName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Torrent Manager
DefaultGroupName=Torrent Manager
OutputDir=dist\installer
OutputBaseFilename=TorrentManager-Setup-v0.7
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
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
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Options:"; Flags: unchecked
Name: "startup"; Description: "Start Torrent Manager with Windows"; Flags: unchecked
Name: "close_to_tray"; Description: "Keep running in the notification area when closing the window"; Flags: unchecked
[Files]
Source: "dist\TorrentManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\Torrent Manager"; Filename: "{app}\TorrentManager.exe"
[INI]
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "language"; String: "{language}"
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "desktopicon"; String: "{code:DesktopValue}"
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "startup"; String: "{code:StartupValue}"
Filename: "{app}\install-defaults.ini"; Section: "Settings"; Key: "close_to_tray"; String: "{code:TrayValue}"
[Run]
Filename: "{app}\TorrentManager.exe"; Description: "Launch Torrent Manager"; Flags: nowait postinstall skipifsilent runasoriginaluser
[UninstallDelete]
Type: filesandordirs; Name: "{app}\browsers"
Type: files; Name: "{app}\install-defaults.ini"
Type: files; Name: "{app}\beallitasok.json"
Type: files; Name: "{app}\kezelt_torrentek.json"
Type: files; Name: "{app}\automatizalas.log"
Type: filesandordirs; Name: "{app}\bithumen_bongeszo_profil"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: dirifempty; Name: "{app}"
[Code]
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
    ((PageID = wpSelectTasks) or (PageID = wpSelectDir) or (PageID = wpSelectProgramGroup));
end;
procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  SetPreviousData(PreviousDataKey, 'Installed', 'yes');
end;
procedure CleanProfile(Profile: String);
var
  Integration, Shortcut: String;
begin
  if (Profile <> '') and DirExists(Profile) then begin
    StringChangeEx(Profile, '%SystemDrive%', GetEnv('SystemDrive'), True);
    Integration := Profile + '\AppData\Local\TorrentManager\windows.ini';
    Shortcut := GetIniString('Windows', 'DesktopShortcut', '', Integration);
    if CompareText(ExtractFileName(Shortcut), 'Torrent Manager.lnk') = 0 then DeleteFile(Shortcut);
    Shortcut := GetIniString('Windows', 'StartupShortcut', '', Integration);
    if CompareText(ExtractFileName(Shortcut), 'Torrent Manager.lnk') = 0 then DeleteFile(Shortcut);
    DelTree(Profile + '\AppData\Local\TorrentManager', True, True, True);
    DelTree(Profile + '\AppData\Roaming\TorrentManager', True, True, True);
    DeleteFile(Profile + '\Desktop\Torrent Manager.lnk');
    DeleteFile(Profile + '\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Torrent Manager.lnk');
  end;
end;
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Names: TArrayOfString;
  I: Integer;
  Profile: String;
begin
  if CurUninstallStep = usPostUninstall then begin
    if RegGetSubkeyNames(HKLM, 'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList', Names) then
      for I := 0 to GetArrayLength(Names)-1 do
        if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\' + Names[I], 'ProfileImagePath', Profile) then
          CleanProfile(Profile);
    if RegGetSubkeyNames(HKU, '', Names) then
      for I := 0 to GetArrayLength(Names)-1 do begin
        RegDeleteKeyIncludingSubkeys(HKU, Names[I] + '\Software\TorrentManager');
        RegDeleteValue(HKU, Names[I] + '\Software\Microsoft\Windows\CurrentVersion\Run', 'TorrentManager');
      end;
    RegDeleteKeyIncludingSubkeys(HKCU, 'Software\TorrentManager');
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'TorrentManager');
  end;
end;
