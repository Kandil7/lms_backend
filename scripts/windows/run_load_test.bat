@echo off
setlocal

set "BASE_URL=%~1"
set "VUS=%~2"
set "DURATION=%~3"
set "HOST_HEADER=%~4"
set "AUTH_ENABLED=%~5"

if "%BASE_URL%"=="" set "BASE_URL=http://localhost:8000"
if "%VUS%"=="" set "VUS=20"
if "%DURATION%"=="" set "DURATION=60s"
if "%HOST_HEADER%"=="" set "HOST_HEADER="
if "%AUTH_ENABLED%"=="" set "AUTH_ENABLED=false"

k6 run tests/perf/k6_smoke.js ^
  -e BASE_URL=%BASE_URL% ^
  -e VUS=%VUS% ^
  -e DURATION=%DURATION% ^
  -e HOST_HEADER=%HOST_HEADER% ^
  -e AUTH_ENABLED=%AUTH_ENABLED%

exit /b %ERRORLEVEL%

