@echo off
cd /d %~dp0frontend
call npm install
if errorlevel 1 exit /b 1
call npm run build
if errorlevel 1 exit /b 1
copy /Y ..\backend\static_build\index.html ..\backend\templates\index.html >nul
 echo React frontend built. Start Django server from backend folder.
pause
