#define MyAppName "Video Downloader"
#ifndef MyAppVersion
#define MyAppVersion "2.2.0"
#endif
#define MyAppPublisher "Pavlo Tereshchenko"
#define MyAppExeName "VideoDownloader.exe"

[Setup]
AppId={{C7A1A0A5-7F3D-4B4A-9D75-210000000001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Video Downloader
DefaultGroupName=Video Downloader
OutputDir=dist
OutputBaseFilename=VideoDownloader-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "dist\VideoDownloader.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Video Downloader"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Video Downloader"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Video Downloader"; Flags: nowait postinstall skipifsilent
