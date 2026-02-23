@echo off
setlocal

call "%~dp0scripts\windows\stop_demo_proxy_duckdns.bat" %*
exit /b %ERRORLEVEL%
