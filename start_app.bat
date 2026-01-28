@echo off
cd /d "%~dp0"
echo Starting Clause Detection App...
echo Using: launch.ps1
echo.

if not exist "launch.ps1" (
    echo ERROR: launch.ps1 not found.
    pause
    exit /b 1
)

rem Launch in a new PowerShell window and open browser
start "Clause Detection" powershell -ExecutionPolicy Bypass -File "%~dp0launch.ps1"

echo If the browser doesn't open automatically, go to: http://127.0.0.1:5000/
echo Logs (if needed): %~dp0logs\server.out.log and server.err.log
echo.
exit /b 0
