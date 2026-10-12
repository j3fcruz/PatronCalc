#define AppName "PatronCalc"
#define AppVersion "1.4.0"
#define AppPublisher "PatronHubDevs"
[Setup]
AppId={{B9529901-5F02-40B7-9F8C-9254E66E879E}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\PatronCalc
DefaultGroupName=PatronCalc
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=PatronCalc-Setup-1.4.0
SetupIconFile=..\assets\patroncalc.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\PatronCalc.exe
ArchitecturesAllowed=x64compatible
[Files]
Source: "..\build\calculator.dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
[Icons]
Name: "{autoprograms}\PatronCalc"; Filename: "{app}\PatronCalc.exe"
Name: "{autodesktop}\PatronCalc"; Filename: "{app}\PatronCalc.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; Flags: unchecked
[Run]
Filename: "{app}\PatronCalc.exe"; Description: "Launch PatronCalc"; Flags: nowait postinstall skipifsilent
