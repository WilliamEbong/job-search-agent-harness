@echo off
rem Double-click to install or update Candor. See README "Get the app (no terminal)".
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\install.ps1"
echo.
pause
