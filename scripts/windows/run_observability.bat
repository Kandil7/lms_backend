@echo off
setlocal

call "%~dp0scripts\run_observability.bat" %*
exit /b %errorlevel%

