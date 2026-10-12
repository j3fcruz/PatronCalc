@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist "build\calculator.dist\PatronCalc.exe" (
  echo [ERROR] Build application with BUILD_WINDOWS.bat first.
  exit /b 1
)
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo [ERROR] Inno Setup 6 not found. Install from https://jrsoftware.org/isinfo.php
  exit /b 1
)
"%ISCC%" "installer\PatronCalc.iss"
if errorlevel 1 exit /b 1
echo [PASS] Installer build completed in installer\output
exit /b 0
