@echo off
setlocal

if /I "%~1"=="--help" (
  echo Usage: %~nx0 [--logs]
  echo.
  echo Starts demo reverse proxy ^(Caddy^) + DuckDNS updater.
  echo Requires side-by-side demo API running on http://localhost:8002
  exit /b 0
)

set "PROJECT_NAME=lms-demo-proxy"
set "COMPOSE_FILE=docker-compose.demo.proxy.yml"
set "ENV_FILE=.env.demo.proxy"
set "ENV_EXAMPLE=.env.demo.proxy.example"
set "DEMO_DOMAIN="
set "LETSENCRYPT_EMAIL="
set "DUCKDNS_TOKEN="

if not exist "%ENV_FILE%" (
  if exist "%ENV_EXAMPLE%" (
    copy /Y "%ENV_EXAMPLE%" "%ENV_FILE%" >nul
    echo [demo-proxy] Created %ENV_FILE% from %ENV_EXAMPLE%
    echo [demo-proxy] Edit %ENV_FILE% and set your real values, then rerun.
    exit /b 1
  ) else (
    echo [demo-proxy] Missing %ENV_EXAMPLE%
    exit /b 1
  )
)

for /f "tokens=1,* delims==" %%A in ('findstr /B /I "DEMO_DOMAIN=" "%ENV_FILE%"') do set "DEMO_DOMAIN=%%B"
for /f "tokens=1,* delims==" %%A in ('findstr /B /I "LETSENCRYPT_EMAIL=" "%ENV_FILE%"') do set "LETSENCRYPT_EMAIL=%%B"
for /f "tokens=1,* delims==" %%A in ('findstr /B /I "DUCKDNS_TOKEN=" "%ENV_FILE%"') do set "DUCKDNS_TOKEN=%%B"

if "%DEMO_DOMAIN%"=="" (
  echo [demo-proxy] DEMO_DOMAIN is empty in %ENV_FILE%
  exit /b 1
)

if "%LETSENCRYPT_EMAIL%"=="" (
  echo [demo-proxy] LETSENCRYPT_EMAIL is empty in %ENV_FILE%
  exit /b 1
)

if "%DUCKDNS_TOKEN%"=="" (
  echo [demo-proxy] DUCKDNS_TOKEN is empty in %ENV_FILE%
  exit /b 1
)

if /I "%DUCKDNS_TOKEN%"=="change-me" (
  echo [demo-proxy] Replace DUCKDNS_TOKEN=change-me in %ENV_FILE%
  exit /b 1
)

echo [demo-proxy] Starting reverse proxy + DuckDNS updater...
docker compose -p "%PROJECT_NAME%" --env-file "%ENV_FILE%" -f "%COMPOSE_FILE%" up -d
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo [demo-proxy] Ready:
echo              Domain: https://%DEMO_DOMAIN%
echo              Upstream: http://localhost:8002
echo              Readiness: https://%DEMO_DOMAIN%/api/v1/ready
echo.
echo [demo-proxy] Stop command:
echo              scripts\windows\stop_demo_proxy_duckdns.bat

if /I "%~1"=="--logs" (
  docker compose -p "%PROJECT_NAME%" --env-file "%ENV_FILE%" -f "%COMPOSE_FILE%" logs -f demo-caddy duckdns
)

exit /b 0
