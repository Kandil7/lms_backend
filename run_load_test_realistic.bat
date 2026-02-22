@echo off
setlocal

call "%~dp0scripts\run_load_test_realistic.bat" %*
exit /b %errorlevel%

