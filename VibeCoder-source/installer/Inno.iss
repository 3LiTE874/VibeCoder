; VibeCoder Windows installer.
; Requires Inno Setup 6: https://jrsoftware.org/isinfo.php
;
; Build order, from the VibeCoder-source folder:
;   .venv\Scripts\python.exe -m pip install pyinstaller
;   .venv\Scripts\pyinstaller.exe --noconfirm installer\VibeCoder.spec
;   ISCC.exe installer\Inno.iss
;
; Or run installer\build.ps1, which does those steps.
; Version below must stay in step with src\vibecoder\__init__.py.

#define MyAppName "VibeCoder"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Christopher LePage"
#define MyAppURL "https://github.com/3LiTE874/VibeCoder"
#define MyAppExeName "VibeCoder.exe"
#define DistDir "..\dist\VibeCoder"
#define SourceRoot ".."

#ifexist SourcePath + "..\dist\VibeCoder\VibeCoder.exe"
#else
  #error "dist\VibeCoder\VibeCoder.exe was not found. Build it with PyInstaller before compiling this script."
#endif

[Setup]
AppId={{C99D92B6-3705-4D87-85AC-A6793E37C54F}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppComments=Notepad++-style editor. Source code: {#MyAppURL}
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=VibeCoder Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}.0
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile={#SourceRoot}\LICENSE
OutputDir=Output
OutputBaseFilename=VibeCoder-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceRoot}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceRoot}\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
