## v1.4.2 Layout hotfix

Fixed clipped Programmer Mode controls and white scroll-panel background. Six-column keyboard gets extra width when screen permits, and long HEX/BIN values use horizontally scrollable read-only fields. The vertical scrollbar remains available on short screens.

# PatronCalc v1.4 — Windows Integration

Complete cumulative source: Standard, Scientific and Programmer modes from v1.3, plus Windows icon, preferences (theme, startup mode, always-on-top), robust Nuitka standalone build, and optional Inno Setup 6 per-user installer.

## Quick start (Windows)
1. Run `INSTALL_WINDOWS.bat`.
2. Run `START_WINDOWS.bat`.
3. Click the gear icon to configure the theme, startup mode, and always-on-top.
4. Run `RUN_TESTS_WINDOWS.bat` to test calculation logic.

## Windows distribution
1. Run `BUILD_WINDOWS.bat` to generate `build\calculator.dist\PatronCalc.exe` (standalone DIRECTORY; distribute the whole folder).
2. Optionally install Inno Setup **6**, then run `BUILD_INSTALLER_WINDOWS.bat` to generate `installer\output\PatronCalc-Setup-1.4.0.exe`. The installer is per-user and requires no elevation.
3. Test the built program and the installer on a clean Windows account before release. Binary compilation and signing are not performed in this source package. Windows SmartScreen can warn about unsigned apps.

## Data and safety
User preferences and history remain under the Windows per-user application-data directory. The installer uninstall does NOT remove these files. Existing v1.3 configuration is reused; settings are added compatibly. No administrator rights or internet connection are needed to run the compiled app. All calculations use restricted parsers; no eval or exec.

## Requirements
Windows 10/11 x64, Python 3.10+ for running from source, PySide6; Nuitka build dependencies installed by the build script. Avoid overwriting a verified v1.3 until v1.4 is tested on the target PC.


### v1.4.1 Auto-fit fix
Programmer keypad now lives inside a vertical scroll container to prevent button overlap at small resolutions and Windows display scaling. The main window expands automatically when switching to Programmer/Scientific mode if screen space allows. On shorter screens, scroll to reach the last row.
