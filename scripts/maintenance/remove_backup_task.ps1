param(
    [string]$TaskName = "LMS-DB-Backup"
)

$ErrorActionPreference = "Stop"

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Scheduled task '$TaskName' removed."
}
catch {
    Write-Warning "Failed to remove task '$TaskName': $($_.Exception.Message)"
    exit 1
}

