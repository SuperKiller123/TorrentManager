#define MyAppName "Torrent Manager"
#define MyAppVersion "0.4.0"
#define MyAppExeName "TorrentManager.exe"

[Setup]
AppId={{4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Torrent Manager Project
DefaultDirName={localappdata}\Programs\Torrent Manager
DefaultGroupName=Torrent Manager
OutputDir=dist\installer
OutputBaseFilename=TorrentManager-Setup-v0.4.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
UninstallDisplayIcon={app}\TorrentManager.exe
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "hungarian"; MessagesFile: "compiler:Languages\Hungarian.isl"

[Tasks]
Name: "desktopicon"; Description: "Asztali parancsikon létrehozása"; GroupDescription: "További lehetőségek:"; Flags: unchecked

[Files]
Source: "dist\TorrentManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Torrent Manager"; Filename: "{app}\TorrentManager.exe"
Name: "{autodesktop}\Torrent Manager"; Filename: "{app}\TorrentManager.exe"; Tasks: desktopicon

[Run]
; Telepítés után nem indul el automatikusan.
