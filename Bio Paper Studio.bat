@echo off
rem Starts Bio Paper Studio on this PC only (http://127.0.0.1:8765). Close this window to stop it.
set "APP=%USERPROFILE%\.claude\skills\paper-studio\app\server.py"
where py >nul 2>nul && (py -3 "%APP%" & goto :eof)
python "%APP%"
if errorlevel 1 pause
