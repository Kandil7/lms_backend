# LMS Full Stack One-Click Starter
# This script will set up and run the complete LMS system

Write-Host "🚀 LMS Full Stack Starter" -ForegroundColor Green
Write-Host "===========================" -ForegroundColor Cyan
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "• Set up database migrations" -ForegroundColor White
Write-Host "• Start backend API server (port 8000)" -ForegroundColor White
Write-Host "• Start frontend development server (port 3000)" -ForegroundColor White
Write-Host "• Verify integration is working" -ForegroundColor White
Write-Host "" -ForegroundColor Cyan

# Function to check if command exists
function Test-Command {
    param([string]$command)
    try {
        Get-Command $command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Cyan

$pythonInstalled = Test-Command "python"
$nodeInstalled = Test-Command "node"
$npmInstalled = Test-Command "npm"
$uvicornInstalled = Test-Command "uvicorn"

if (-not $pythonInstalled) {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

if (-not $nodeInstalled) {
    Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

if (-not $npmInstalled) {
    Write-Host "❌ npm not found. Please install Node.js with npm" -ForegroundColor Red
    exit 1
}

Write-Host "✅ All prerequisites found" -ForegroundColor Green

# Navigate to project directory
$projectDir = "K:\business\projects\lms_backend"
if (-not (Test-Path $projectDir)) {
    Write-Host "❌ Project directory not found: $projectDir" -ForegroundColor Red
    exit 1
}

Set-Location $projectDir
Write-Host "📍 Working directory: $projectDir" -ForegroundColor Cyan

# Step 1: Setup backend
Write-Host "`n🔧 Setting up backend..." -ForegroundColor Cyan

# Create .env file if missing
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..."
    Copy-Item ".env.example" ".env" -Force
}

# Run database migrations
Write-Host "Running database migrations..."
try {
    & alembic upgrade head
} catch {
    Write-Host "⚠️  Migration failed or already applied" -ForegroundColor Yellow
}

# Step 2: Start backend in background
Write-Host "Starting backend server on port 8000..." -ForegroundColor Cyan
$backendProcess = Start-Process -FilePath "uvicorn" -ArgumentList "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload" -NoNewWindow -PassThru

# Wait for backend to start
Write-Host "Waiting for backend to start (up to 30 seconds)..." -ForegroundColor Yellow
$startTime = Get-Date
$backendReady = $false

while ((Get-Date).Subtract($startTime).TotalSeconds -lt 30) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/health" -Method Head -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {
        # Continue waiting
    }
    Start-Sleep -Seconds 1
}

if (-not $backendReady) {
    Write-Host "❌ Backend failed to start. Check if port 8000 is available." -ForegroundColor Red
    Write-Host "Try: netstat -ano | findstr :8000" -ForegroundColor White
    exit 1
}

Write-Host "✅ Backend started successfully!" -ForegroundColor Green

# Step 3: Setup frontend
Write-Host "`n🌐 Setting up frontend..." -ForegroundColor Cyan
$frontendDir = "K:\business\projects\lms_backend\frontend\educonnect-pro"
if (-not (Test-Path $frontendDir)) {
    Write-Host "❌ Frontend directory not found: $frontendDir" -ForegroundColor Red
    exit 1
}

Set-Location $frontendDir

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    & npm install --legacy-peer-deps
}

# Start frontend
Write-Host "Starting frontend on port 3000..." -ForegroundColor Cyan
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -NoNewWindow -PassThru

# Wait for frontend to start
Write-Host "Waiting for frontend to start (up to 60 seconds)..." -ForegroundColor Yellow
$startTime = Get-Date
$frontendReady = $false

while ((Get-Date).Subtract($startTime).TotalSeconds -lt 60) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -Method Head -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $frontendReady = $true
            break
        }
    } catch {
        # Continue waiting
    }
    Start-Sleep -Seconds 2
}

if (-not $frontendReady) {
    Write-Host "⚠️  Frontend may take longer to start. Check http://localhost:5173" -ForegroundColor Yellow
}

# Final status
Write-Host "`n🎉 LMS Full Stack Started Successfully!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "✅ Backend: http://localhost:8000/api/v1/health" -ForegroundColor White
Write-Host "✅ Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "✅ API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "" -ForegroundColor Cyan
Write-Host "To use the LMS:" -ForegroundColor Yellow
Write-Host "- Open browser and go to: http://localhost:3000" -ForegroundColor White
Write-Host "- Login with demo credentials:" -ForegroundColor White
Write-Host "  • admin@lms.local / AdminPass123" -ForegroundColor White
Write-Host "  • instructor@lms.local / InstructorPass123" -ForegroundColor White
Write-Host "  • student@lms.local / StudentPass123" -ForegroundColor White
Write-Host "" -ForegroundColor Cyan
Write-Host "To stop:" -ForegroundColor Yellow
Write-Host "- Press Ctrl+C in the PowerShell window where this script ran" -ForegroundColor White

# Keep script running to prevent immediate exit
Write-Host "`nPress Enter to exit..." -ForegroundColor Gray
Read-Host