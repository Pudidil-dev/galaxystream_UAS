; Inno Setup Script for GalaxyStream
; Download Inno Setup: https://jrsoftware.org/isdl.php

#define MyAppName "GalaxyStream"
#define MyAppVersion "4"
#define MyAppPublisher "GalaxyStream Team"
#define MyAppExeName "GalaxyStream.exe"
#define MyServerExeName "wajik-anime-api.exe"

[Setup]
; App information
AppId={{GalaxyStream-4.0}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output configuration
OutputDir=installer_output
OutputBaseFilename=GalaxyStream_Setup_v{#MyAppVersion}
SetupIconFile=galaxystream_icon_fix.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Uninstaller
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "addfirewall"; Description: "Allow local server (port 3001) through Windows Firewall"; GroupDescription: "Additional Options"; Flags: unchecked

[Files]
; Include all files from dist/GalaxyStream folder
Source: "dist\GalaxyStream\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; Desktop shortcut (if selected)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; Uninstaller in Start Menu
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; Option to run app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
; Optional: add firewall rule for local API server
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""GalaxyStream Local API"" dir=in action=allow protocol=TCP localport=3001"; Flags: runhidden; Tasks: addfirewall

[UninstallRun]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""GalaxyStream Local API"""; Flags: runhidden

[Code]
// Optional: Check if app is running before uninstall
function InitializeSetup(): Boolean;
var
  ErrorCode: Integer;
begin
  // Kill running processes before install
  Exec('taskkill', '/F /IM {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Exec('taskkill', '/F /IM {#MyServerExeName}', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Result := True;
end;

function InitializeUninstall(): Boolean;
var
  ErrorCode: Integer;
begin
  // Kill GalaxyStream process if running
  Exec('taskkill', '/F /IM {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Exec('taskkill', '/F /IM {#MyServerExeName}', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  Result := True;
end;
