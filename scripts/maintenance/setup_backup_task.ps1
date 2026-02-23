param(
    [string]$TaskName = "LMS-DB-Backup",
    [string]$Time = "02:00"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..\..")
$backupScript = Join-Path $projectRoot "scripts\windows\backup_db.bat"

if (-not (Test-Path $backupScript)) {
    throw "backup_db.bat not found at $backupScript"
}

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$backupScript`""
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel LeastPrivilege
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable

$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings
Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null

Write-Host "Scheduled task '$TaskName' created (daily at $Time)."
Write-Host "Command: $backupScript"

