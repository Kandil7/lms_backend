@echo off
echo Starting LMS Full Stack...

:: Set up backend
echo.
echo 1. Setting up backend...
cd /d K:\business\projects\lms_backend
if not exist .env (
    echo Copying .env.example to .env
    copy .env.example .env
)

echo Running database migrations...
alembic upgrade head

echo Starting backend server...
start "" cmd /c "uvicorn app.main:app --reload  --port 8000"

:: Wait for backend to start
timeout /t 10 /nobreak >nul

:: Start frontend
echo.
echo 2. Starting frontend...
cd /d K:\business\projects\lms_backend\frontend\educonnect-pro
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install --legacy-peer-deps
)

echo Starting frontend development server...
start "" cmd /c "npm run dev"

echo.
echo LMS Full Stack started successfully!
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000
echo - API Health: http://localhost:8000/api/v1/health
echo.
echo Press any key to exit...
pause >nul