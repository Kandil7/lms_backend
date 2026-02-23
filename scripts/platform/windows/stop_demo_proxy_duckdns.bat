@echo off
setlocal

set "PROJECT_NAME=lms-demo-proxy"
set "COMPOSE_FILE=docker-compose.demo.proxy.yml"
set "ENV_FILE=.env.demo.proxy"
set "ENV_EXAMPLE=.env.demo.proxy.example"
set "ENV_ARGS="
set "PURGE_FLAG="

if /I "%~1"=="--purge" (
  set "PURGE_FLAG=-v"
)

if exist "%ENV_FILE%" (
  set "ENV_ARGS=--env-file %ENV_FILE%"
) else if exist "%ENV_EXAMPLE%" (
  set "ENV_ARGS=--env-file %ENV_EXAMPLE%"
)

docker compose -p "%PROJECT_NAME%" %ENV_ARGS% -f "%COMPOSE_FILE%" down %PURGE_FLAG%
exit /b %ERRORLEVEL%
