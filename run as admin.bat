@echo off
echo Running Desktop App as Administrator...
echo.
echo This will run the desktop app with elevated privileges.
echo Administrator rights might be needed for global keyboard monitoring.
echo.
pause

powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && npm run desktop-start' -Verb RunAs"

pause 