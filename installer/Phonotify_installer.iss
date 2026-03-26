[Setup]
AppName=Phonotify
AppVersion=1.0
DefaultDirName={pf}\Phonotify
DefaultGroupName=Phonotify
OutputBaseFilename=Phonotify_Installer
Compression=lzma
SolidCompression=yes

# Change to 'yes' to require admin rights during install
PrivilegesRequired=admin

[Files]
; Main executable produced by PyInstaller
Source: "dist\\Phonotify.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Phonotify"; Filename: "{app}\Phonotify.exe"
Name: "{userstartup}\Phonotify (Run at startup)"; Filename: "{app}\Phonotify.exe"; Tasks: startupicon

[Tasks]
Name: "startupicon"; Description: "Create shortcut in Startup folder"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\Phonotify.exe"; Description: "Run Phonotify"; Flags: nowait postinstall skipifsilent

; To compile: run Inno Setup Compiler (ISCC.exe) or use these commands in a Windows environment with Inno installed:
; ISCC.exe "Phonotify_installer.iss"
