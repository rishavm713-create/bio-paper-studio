@echo off
rem Installs Bio Paper Studio: Python and Claude Code if missing, the app, references and a Desktop shortcut.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
pause
