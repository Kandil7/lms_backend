@echo off
setlocal

set "PS_SCRIPT=%~dp0..\maintenance\run_restore_drill.ps1"
if not exist "%PS_SCRIPT%" (
  echo [restore_drill] Missing script: %PS_SCRIPT%
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %*
exit /b %ERRORLEVEL%

