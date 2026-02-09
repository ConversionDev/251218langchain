@echo off
REM Run Flutter app on Android emulator (Cursor)
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0run_android.ps1"
exit /b %ERRORLEVEL%
