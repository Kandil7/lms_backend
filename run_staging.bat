@echo off
setlocal

call "%~dp0scripts\run_staging.bat" %*
exit /b %errorlevel%

