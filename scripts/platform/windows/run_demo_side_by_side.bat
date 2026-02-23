@echo off
setlocal

call "%~dp0scripts\windows\run_demo_side_by_side.bat" %*
exit /b %ERRORLEVEL%
