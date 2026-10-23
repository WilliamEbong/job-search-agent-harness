@echo off
rem Double-click to open Candor without the Desktop shortcut. Run "Install Candor" first.
cd /d "%~dp0"
start "" pythonw -m app.launcher
