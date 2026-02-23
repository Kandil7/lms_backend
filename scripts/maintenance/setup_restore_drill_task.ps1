param(
    [string]$TaskName = "LMS-DB-Restore-Drill",
    [string]$Time = "03:30",
    [string]$DaysOfWeek = "Sunday",
    [string]$ComposeFile = "docker-compose.prod.yml"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$drillScript = Join-Path $scriptDir "run_restore_drill.ps1"

if (-not (Test-Path $drillScript)) {
    throw "run_restore_drill.ps1 not found at $drillScript"
}

$dayTokens = $DaysOfWeek.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
if ($dayTokens.Count -eq 0) {
    throw "DaysOfWeek cannot be empty. Example: Sunday or Sunday,Wednesday"
}

$actionArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$drillScript`" -ComposeFile `"$ComposeFile`""
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs
$trigger = New-ScheduledTaskTrigger -Weekly -At $Time -DaysOfWeek $dayTokens
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel LeastPrivilege
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable

$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings
Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null

Write-Host "Scheduled restore drill task '$TaskName' created."
Write-Host "Schedule: $DaysOfWeek at $Time"
Write-Host "Compose file: $ComposeFile"

