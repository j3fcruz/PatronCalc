@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (py calculator.py) else (python calculator.py)
if errorlevel 1 pause
