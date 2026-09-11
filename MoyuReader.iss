; MoyuReader Windows 安装包脚本
; 编译: ISCC.exe MoyuReader.iss  (或用 Inno Setup GUI 打开编译)

[Setup]
AppName=MoyuReader
AppVersion=0.2.1
AppPublisher=MoyuReader
DefaultDirName={autopf}\MoyuReader
DefaultGroupName=MoyuReader
OutputDir=installer
OutputBaseFilename=MoyuReader-Setup-0.2.1
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\MoyuReader.exe
WizardStyle=modern
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"

[Files]
Source: "dist\MoyuReader.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\摸鱼小说阅读器"; Filename: "{app}\MoyuReader.exe"
Name: "{autodesktop}\摸鱼小说阅读器"; Filename: "{app}\MoyuReader.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MoyuReader.exe"; Description: "立即运行摸鱼小说阅读器"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
; 卸载不删除 %APPDATA%\MoyuReader（保留书架与进度）
Type: files; Name: "{app}\*.log"
