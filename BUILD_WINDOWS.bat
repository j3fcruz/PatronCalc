@echo off
setlocal EnableExtensions
cd /d "%~dp0"
where py >nul 2>nul || (echo [ERROR] Python launcher py not found. & exit /b 1)
py -m pip install -r requirements.txt "Nuitka>=2.4" ordered-set zstandard
if errorlevel 1 goto fail
py -m nuitka --standalone --enable-plugin=pyside6 --windows-console-mode=disable --windows-icon-from-ico="assets\patroncalc.ico" --include-data-files="assets\patroncalc.ico=assets/patroncalc.ico" --output-dir=build --output-filename=PatronCalc.exe calculator.py
if errorlevel 1 goto fail
if not exist "build\calculator.dist\PatronCalc.exe" goto fail
if not exist "build\calculator.dist\assets\patroncalc.ico" goto fail
echo [PASS] build\calculator.dist\PatronCalc.exe
echo [INFO] Run BUILD_INSTALLER_WINDOWS.bat for optional setup executable.
exit /b 0
:fail
echo [FAIL] Build could not be verified. Check errors above.
exit /b 1
