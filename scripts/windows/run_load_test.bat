@echo off
setlocal

call "%~dp0scripts\run_load_test.bat" %*
exit /b %errorlevel%

