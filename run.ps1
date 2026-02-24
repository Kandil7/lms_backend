#!/usr/bin/env pwsh
# LMS Backend Run Script
# Usage: .\run.ps1 [-Mode <mode>] [-Help]
# Modes: docker, dev, debug, migrate

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("docker", "dev", "debug", "migrate", "help")]
    [string]$Mode = "docker",
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

# Function to display help
function Show-Help {
    Write-Host "LMS Backend Run Script" -ForegroundColor Cyan
    Write-Host "Usage: .\run.ps1 [-Mode <mode>] [-Help]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Modes:" -ForegroundColor Green
    Write-Host "  docker    : Run with Docker Compose (default) - starts API, DB, Redis"
    Write-Host "  dev       : Run development server directly with uvicorn (no Docker)"
    Write-Host "  debug     : Run with debug mode and auto-reload"
    Write-Host "  migrate   : Run database migrations only"
    Write-Host "  help      : Show this help message"
    Write-Host ""
    Write-Host "Environment:" -ForegroundColor Green
    Write-Host "  Copy .env.example to .env and customize for your environment"
    Write-Host "  Required services: PostgreSQL, Redis (or use docker-compose.yml)"
}

# Check if help is requested
if ($Help.IsPresent) {
    Show-Help
    exit 0
}

# Validate environment
if (-not (Test-Path ".env")) {
    Write-Warning "Warning: .env file not found. Copy .env.example to .env first."
    Write-Host "Creating .env from .env.example..."
    Copy-Item ".env.example" ".env" -Force
}

# Function to check if Docker is available
function Test-Docker {
    try {
        $dockerVersion = docker --version 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# Function to check if Python is available
function Test-Python {
    try {
        $pythonVersion = python --version 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# Main execution based on mode
switch ($Mode) {
    "docker" {
        Write-Host "🚀 Starting LMS Backend with Docker Compose..." -ForegroundColor Cyan
        
        if (-not (Test-Docker)) {
            Write-Error "Docker not found. Please install Docker Desktop."
            exit 1
        }
        
        # Start services with docker-compose
        Write-Host "Starting PostgreSQL, Redis, and API services..."
        docker-compose up --build
    }
    
    "dev" {
        Write-Host "💻 Running LMS Backend in development mode..." -ForegroundColor Cyan
        
        if (-not (Test-Python)) {
            Write-Error "Python not found. Please install Python 3.9+."
            exit 1
        }
        
        # Install dependencies if not already installed
        if (-not (Test-Path "venv")) {
            Write-Host "Creating virtual environment..."
            python -m venv venv
        }
        
        # Activate virtual environment and install dependencies
        Write-Host "Installing dependencies..."
        & venv\Scripts\pip install -r requirements.txt
        
        # Run the FastAPI app
        Write-Host "Starting FastAPI server on http://localhost:8000..."
        & venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    }
    
    "debug" {
        Write-Host "🔍 Running LMS Backend in debug mode..." -ForegroundColor Cyan
        
        if (-not (Test-Python)) {
            Write-Error "Python not found. Please install Python 3.9+."
            exit 1
        }
        
        # Install dependencies
        if (-not (Test-Path "venv")) {
            Write-Host "Creating virtual environment..."
            python -m venv venv
        }
        
        Write-Host "Installing dependencies..."
        & venv\Scripts\pip install -r requirements.txt
        
        # Run with debug settings
        Write-Host "Starting FastAPI server in debug mode on http://localhost:8000..."
        $env:DEBUG="true"
        $env:LOG_LEVEL="DEBUG"
        & venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
    }
    
    "migrate" {
        Write-Host "🔧 Running database migrations..." -ForegroundColor Cyan
        
        if (-not (Test-Python)) {
            Write-Error "Python not found. Please install Python 3.9+."
            exit 1
        }
        
        # Install dependencies
        if (-not (Test-Path "venv")) {
            Write-Host "Creating virtual environment..."
            python -m venv venv
        }
        
        Write-Host "Installing dependencies..."
        & venv\Scripts\pip install -r requirements.txt
        
        # Run alembic migrations
        Write-Host "Running database migrations..."
        & venv\Scripts\alembic upgrade head
    }
    
    "help" {
        Show-Help
        exit 0
    }
    
    default {
        Write-Error "Unknown mode: $Mode"
        Show-Help
        exit 1
    }
}