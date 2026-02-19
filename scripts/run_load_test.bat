@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
if not defined PROJECT_ROOT (
    echo ERROR: Failed to resolve project root.
    exit /b 1
)

set "BASE_URL=http://localhost:8000"
set "VUS=10"
set "DURATION=30s"
set "HOST_HEADER="
set "AUTH_ENABLED=false"

if not "%~1"=="" set "BASE_URL=%~1"
if not "%~2"=="" set "VUS=%~2"
if not "%~3"=="" set "DURATION=%~3"
if not "%~4"=="" set "HOST_HEADER=%~4"
if not "%~5"=="" set "AUTH_ENABLED=%~5"

set "K6_SCRIPT=%PROJECT_ROOT%\tests\perf\k6_smoke.js"
if not exist "%K6_SCRIPT%" (
    echo ERROR: Missing k6 script: %K6_SCRIPT%
    exit /b 1
)

where k6 >nul 2>&1
if "%errorlevel%"=="0" (
    echo.
    echo ==^> Running load test with local k6
    echo BASE_URL=%BASE_URL% VUS=%VUS% DURATION=%DURATION% HOST_HEADER=%HOST_HEADER% AUTH_ENABLED=%AUTH_ENABLED%
    k6 run -e BASE_URL=%BASE_URL% -e VUS=%VUS% -e DURATION=%DURATION% -e HOST_HEADER=%HOST_HEADER% -e AUTH_ENABLED=%AUTH_ENABLED% "%K6_SCRIPT%"
    exit /b %errorlevel%
)

echo.
echo ==^> k6 not found locally, running with Docker image
echo BASE_URL (from container) defaults to host.docker.internal
if "%BASE_URL%"=="http://localhost:8000" (
  set "BASE_URL=http://host.docker.internal:8000"
  if "%HOST_HEADER%"=="" set "HOST_HEADER=localhost"
)
echo BASE_URL=%BASE_URL% VUS=%VUS% DURATION=%DURATION% HOST_HEADER=%HOST_HEADER% AUTH_ENABLED=%AUTH_ENABLED%

docker run --rm -i ^
  --add-host=host.docker.internal:host-gateway ^
  -v "%PROJECT_ROOT%\tests\perf:/scripts" ^
  -e BASE_URL=%BASE_URL% ^
  -e VUS=%VUS% ^
  -e DURATION=%DURATION% ^
  -e HOST_HEADER=%HOST_HEADER% ^
  -e AUTH_ENABLED=%AUTH_ENABLED% ^
  grafana/k6 run /scripts/k6_smoke.js

exit /b %errorlevel%
