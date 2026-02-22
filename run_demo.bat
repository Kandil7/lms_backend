@echo off
setlocal

call "%~dp0scripts\run_demo.bat" %*
exit /b %errorlevel%
