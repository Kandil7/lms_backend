@echo off
setlocal

call "%~dp0scripts\restore_db.bat" %*
exit /b %errorlevel%

