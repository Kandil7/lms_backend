@echo off
echo Starting LMS Backend Production Deployment...

cd /d "%~dp0\.."

echo Step 1: Applying database migrations...
alembic upgrade head

if %errorlevel% neq 0 (
    echo ERROR: Database migration failed!
    exit /b 1
)
echo SUCCESS: Database migrations applied successfully

echo Step 2: Building frontend...
cd frontend\educonnect-pro
npm install --production
npm run build
cd ..\..

if %errorlevel% neq 0 (
    echo ERROR: Frontend build failed!
    exit /b 1
)
echo SUCCESS: Frontend built successfully

echo Step 3: Deploying Docker containers...
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

if %errorlevel% neq 0 (
    echo ERROR: Docker deployment failed!
    exit /b 1
)
echo SUCCESS: Docker containers deployed successfully

echo Step 4: Verifying deployment...
echo Checking health endpoint:
curl -s -o nul -w "HTTP status: %{http_code}" http://localhost:8000/api/v1/ready

echo Production deployment completed successfully!
echo Please verify the new instructor and admin endpoints:
echo - POST /api/v1/instructors/register
echo - POST /api/v1/admin/setup
echo - GET /api/v1/instructors/onboarding-status  
echo - GET /api/v1/admin/onboarding-status

echo Swagger UI available at: https://egylms.duckdns.org/docs
echo Note: API docs are disabled in production by default (ENABLE_API_DOCS=false)

pause