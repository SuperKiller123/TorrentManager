#define MyAppName "Torrent Manager"
#define MyAppVersion "0.6.0"
#define MyAppExeName "TorrentManager.exe"

[Setup]
AppId={{4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Torrent Manager Project
DefaultDirName={localappdata}\Programs\Torrent Manager
DefaultGroupName=Torrent Manager
OutputDir=dist\installer
OutputBaseFilename=TorrentManager-Setup-v0.6.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
UninstallDisplayIcon={app}\TorrentManager.exe
SetupIconFile=assets\app_icon.ico
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
UsePreviousGroup=yes
UsePreviousTasks=yes
UsePreviousLanguage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "hungarian"; MessagesFile: "compiler:Languages\Hungarian.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop shortcut / Asztali parancsikon"; GroupDescription: "Additional tasks / További lehetőségek:"; Flags: unchecked

[Files]
Source: "dist\TorrentManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Torrent Manager"; Filename: "{app}\TorrentManager.exe"
Name: "{autodesktop}\Torrent Manager"; Filename: "{app}\TorrentManager.exe"; Tasks: desktopicon

[Code]
var
  LanguagePage: TInputOptionWizardPage;
  PreviouslyInstalled: Boolean;

function InitializeSetup: Boolean;
var
  Value: String;
begin
  PreviouslyInstalled := RegQueryStringValue(HKCU,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F}_is1',
    'UninstallString', Value) or RegQueryStringValue(HKLM,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F}_is1',
    'UninstallString', Value);
  Result := True;
end;

function IsUpgrade: Boolean;
begin
  Result := PreviouslyInstalled;
end;

procedure InitializeWizard;
begin
  if not IsUpgrade then begin
    LanguagePage := CreateInputOptionPage(wpSelectDir,
      'Application language / Alkalmazás nyelve',
      'Select the language for the application / Válaszd ki a program nyelvét',
      'You can change the language later in Settings. / Később is módosíthatod a Beállításokban.',
      True, False);
    LanguagePage.Add('English');
    LanguagePage.Add('中文（简体）');
    LanguagePage.Add('हिन्दी');
    LanguagePage.Add('Español');
    LanguagePage.Add('Français');
    LanguagePage.Add('العربية');
    LanguagePage.Add('বাংলা');
    LanguagePage.Add('Português');
    LanguagePage.Add('Русский');
    LanguagePage.Add('اردو');
    LanguagePage.Add('Magyar');
    LanguagePage.Add('Deutsch');
    LanguagePage.SelectedValueIndex := 10;
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := IsUpgrade and ((PageID = wpSelectTasks) or
    (PageID = wpSelectDir) or (PageID = wpSelectProgramGroup));
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Codes: array[0..11] of String;
begin
  if (CurStep = ssPostInstall) and (not IsUpgrade) then begin
    Codes[0] := 'en'; Codes[1] := 'zh'; Codes[2] := 'hi';
    Codes[3] := 'es'; Codes[4] := 'fr'; Codes[5] := 'ar';
    Codes[6] := 'bn'; Codes[7] := 'pt'; Codes[8] := 'ru';
    Codes[9] := 'ur'; Codes[10] := 'hu'; Codes[11] := 'de';
    RegWriteStringValue(HKCU, 'Software\TorrentManager', 'Language',
      Codes[LanguagePage.SelectedValueIndex]);
  end;
end;
