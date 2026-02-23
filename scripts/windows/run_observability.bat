@echo off
setlocal

if not exist ".env.observability" (
  if exist ".env.observability.example" (
    copy /Y ".env.observability.example" ".env.observability" >nul
    echo [run_observability] Created .env.observability from .env.observability.example
  )
)

docker compose -f docker-compose.observability.yml up -d %*
exit /b %ERRORLEVEL%

