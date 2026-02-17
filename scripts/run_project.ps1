param(
    [switch]$NoBuild,
    [switch]$NoMigrate,
    [switch]$SeedDemoData,
    [switch]$CreateAdmin,
    [switch]$FollowLogs
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Ensure-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

Ensure-Command "docker"

Write-Step "Preparing environment file"
if (-not (Test-Path ".env")) {
    if (-not (Test-Path ".env.example")) {
        throw "Missing both '.env' and '.env.example'."
    }
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}
else {
    Write-Host ".env already exists"
}

Write-Step "Starting containers"
$composeArgs = @("compose", "-f", "docker-compose.yml", "up", "-d")
if (-not $NoBuild) {
    $composeArgs += "--build"
}
& docker @composeArgs

if (-not $NoMigrate) {
    Write-Step "Applying database migrations"
    & docker compose -f docker-compose.yml exec -T api alembic upgrade head
}

if ($CreateAdmin) {
    Write-Step "Creating admin user"
    & docker compose -f docker-compose.yml exec -T api python scripts/create_admin.py
}

if ($SeedDemoData) {
    Write-Step "Seeding demo data"
    & docker compose -f docker-compose.yml exec -T api python scripts/seed_demo_data.py
}

Write-Step "Waiting for API health endpoint"
$healthUrl = "http://localhost:8000/api/v1/health"
$healthOk = $false

for ($i = 1; $i -le 30; $i++) {
    try {
        $health = Invoke-RestMethod -Method Get -Uri $healthUrl -TimeoutSec 3
        if ($health.status -eq "ok") {
            $healthOk = $true
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $healthOk) {
    Write-Warning "API health check did not become ready in time. Check logs with: docker compose logs --tail=200 api"
}
else {
    Write-Host "API is healthy at $healthUrl" -ForegroundColor Green
}

Write-Step "Project is running"
Write-Host "API Docs: http://localhost:8000/docs"
Write-Host "ReDoc:    http://localhost:8000/redoc"

if ($FollowLogs) {
    Write-Step "Following API and worker logs (Ctrl+C to stop)"
    & docker compose -f docker-compose.yml logs -f api celery-worker celery-beat
}
