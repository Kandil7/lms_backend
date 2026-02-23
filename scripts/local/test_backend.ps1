# test_backend.ps1
# Quick test to verify backend is running

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -Method Head -TimeoutSec 3
    Write-Host "✅ Backend is running on port 8000" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode)"
} catch {
    Write-Host "❌ Backend not running" -ForegroundColor Red
    Write-Host "Please start backend first with:"
    Write-Host "cd K:\business\projects\lms_backend"
    Write-Host "uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
}