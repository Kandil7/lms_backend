#!/usr/bin/env powershell
# start_lms_full.ps1 - Complete LMS startup script
# Runs both backend and frontend with proper error handling

param(
    [switch]$Force,
    [switch]$NoBackend,
    [switch]$NoFrontend
)

$ErrorActionPreference = "Stop"
$script:exitCode = 0

function Write-Status {
    param([string]$message, [string]$status = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] [$status] $message" -ForegroundColor Cyan
}

function Write-ErrorStatus {
    param([string]$message)
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] [ERROR] $message" -ForegroundColor Red
}

function Test-Port {
    param([string]$ComputerName, [int]$Port)
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect($ComputerName, $Port)
        $tcpClient.Close()
        return $true
    } catch {
        return $false
    }
}

function Start-Backend {
    Write-Status "Starting LMS Backend..."
    
    # Check if already running
    if (Test-Port "localhost" 8000) {
        Write-Status "Backend already running on port 8000" -status "WARNING"
        return $true
    }

    # Navigate to backend directory
    $backendDir = "K:\business\projects\lms_backend"
    if (-not (Test-Path $backendDir)) {
        Write-ErrorStatus "Backend directory not found: $backendDir"
        return $false
    }

    Set-Location $backendDir
    
    # Create .env file if missing
    if (-not (Test-Path ".env")) {
        Write-Status "Creating .env from .env.example"
        Copy-Item ".env.example" ".env" -Force
    }

    # Run database migrations
    Write-Status "Running database migrations..."
    try {
        & alembic upgrade head
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorStatus "Database migration failed"
            return $false
        }
    } catch {
        Write-ErrorStatus "Migration error: $($_.Exception.Message)"
        return $false
    }

    # Start backend server
    Write-Status "Starting backend server on port 8000..."
    $backendProcess = Start-Process -FilePath "uvicorn" -ArgumentList "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" -NoNewWindow -PassThru -ErrorAction Stop
    
    # Wait for backend to start
    $startTime = Get-Date
    while ((Get-Date).Subtract($startTime).TotalSeconds -lt 30) {
        if (Test-Port "localhost" 8000) {
            Write-Status "Backend started successfully!" -status "SUCCESS"
            return $true
        }
        Start-Sleep -Seconds 1
    }

    Write-ErrorStatus "Backend failed to start within 30 seconds"
    return $false
}

function Start-Frontend {
    Write-Status "Starting LMS Frontend..."
    
    # Navigate to frontend directory
    $frontendDir = "K:\business\projects\lms_backend\frontend\educonnect-pro"
    if (-not (Test-Path $frontendDir)) {
        Write-ErrorStatus "Frontend directory not found: $frontendDir"
        return $false
    }

    Set-Location $frontendDir
    
    # Install dependencies if node_modules missing
    if (-not (Test-Path "node_modules")) {
        Write-Status "Installing frontend dependencies..."
        try {
            & npm install --legacy-peer-deps
            if ($LASTEXITCODE -ne 0) {
                Write-ErrorStatus "npm install failed"
                return $false
            }
        } catch {
            Write-ErrorStatus "npm install error: $($_.Exception.Message)"
            return $false
        }
    }

    # Start frontend development server
    Write-Status "Starting frontend on port 5173..."
    $frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -NoNewWindow -PassThru -ErrorAction Stop
    
    # Wait for frontend to start
    $startTime = Get-Date
    while ((Get-Date).Subtract($startTime).TotalSeconds -lt 60) {
        # Check if frontend is accessible (simplified check)
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5173/" -Method Head -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Status "Frontend started successfully!" -status "SUCCESS"
                return $true
            }
        } catch {
            # Continue waiting
        }
        Start-Sleep -Seconds 2
    }

    Write-ErrorStatus "Frontend failed to start within 60 seconds"
    return $false
}

function Show-Instructions {
    Write-Host ""
    Write-Host "LMS Full Stack Startup Complete!" -ForegroundColor Green
    Write-Host "=" * 60
    Write-Host "✅ Backend: http://localhost:8000/api/v1/health"
    Write-Host "✅ Frontend: http://localhost:3000"
    Write-Host "✅ API Docs: http://localhost:8000/docs (development only)"
    Write-Host ""
    Write-Host "To access the LMS:"
    Write-Host "- Open browser and go to: http://localhost:3000"
    Write-Host "- Login with demo credentials:"
    Write-Host "  • admin@lms.local / AdminPass123"
    Write-Host "  • instructor@lms.local / InstructorPass123"
    Write-Host "  • student@lms.local / StudentPass123"
    Write-Host ""
    Write-Host "To stop the servers:"
    Write-Host "- Press Ctrl+C in each PowerShell window"
    Write-Host ""
}

# Main execution
try {
    Write-Status "Starting LMS Full Stack..." -status "INFO"
    
    # Start backend
    if (-not $NoBackend) {
        if (-not (Start-Backend)) {
            Write-ErrorStatus "Failed to start backend"
            $script:exitCode = 1
        }
    }
    
    # Start frontend
    if (-not $NoFrontend) {
        if (-not (Start-Frontend)) {
            Write-ErrorStatus "Failed to start frontend"
            $script:exitCode = 1
        }
    }
    
    if ($script:exitCode -eq 0) {
        Show-Instructions
    }
    
} catch {
    Write-ErrorStatus "Startup error: $($_.Exception.Message)"
    $script:exitCode = 1
}

exit $script:exitCode