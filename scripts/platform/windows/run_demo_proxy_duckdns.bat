@echo off
setlocal

call "%~dp0scripts\windows\run_demo_proxy_duckdns.bat" %*
exit /b %ERRORLEVEL%
