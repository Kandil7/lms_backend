@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_restore_drill.ps1" %*
exit /b %errorlevel%

