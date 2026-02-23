@echo off
setlocal

set "PS_SCRIPT=%~dp0..\helpers\run_project.ps1"
if not exist "%PS_SCRIPT%" (
  echo [run_demo] Missing script: %PS_SCRIPT%
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -SeedDemoData -CreateAdmin -CreateInstructor %*
exit /b %ERRORLEVEL%
