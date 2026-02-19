@echo off
setlocal

call "%~dp0scripts\backup_db.bat" %*
exit /b %errorlevel%

