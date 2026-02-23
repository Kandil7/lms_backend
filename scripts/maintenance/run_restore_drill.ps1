param(
    [string]$ComposeFile = "docker-compose.prod.yml",
    [string]$BackupDir = "backups\db",
    [string]$LogDir = "backups\drill_logs",
    [string]$DrillDbPrefix = "lms_restore_drill",
    [int]$MinExpectedTables = 8,
    [switch]$KeepDrillDatabase
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..\..")

if ([System.IO.Path]::IsPathRooted($ComposeFile)) {
    $composePath = $ComposeFile
}
else {
    $composePath = Join-Path $projectRoot $ComposeFile
}

if (-not (Test-Path $composePath)) {
    throw "Compose file not found: $composePath"
}

if ([System.IO.Path]::IsPathRooted($BackupDir)) {
    $backupDirPath = $BackupDir
}
else {
    $backupDirPath = Join-Path $projectRoot $BackupDir
}

if ([System.IO.Path]::IsPathRooted($LogDir)) {
    $logDirPath = $LogDir
}
else {
    $logDirPath = Join-Path $projectRoot $LogDir
}

New-Item -ItemType Directory -Path $backupDirPath -Force | Out-Null
New-Item -ItemType Directory -Path $logDirPath -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$drillDbName = "${DrillDbPrefix}_${timestamp}"
$logFile = Join-Path $logDirPath "restore_drill_${timestamp}.log"
$backupFileName = $null

function Invoke-Compose {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args,
        [switch]$CaptureOutput
    )

    if ($CaptureOutput) {
        $output = & docker compose -f $composePath @Args
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose command failed: docker compose -f $composePath $($Args -join ' ')"
        }
        return $output
    }

    & docker compose -f $composePath @Args
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose command failed: docker compose -f $composePath $($Args -join ' ')"
    }
}

Start-Transcript -Path $logFile -Force | Out-Null
Write-Host "==> Restore drill started at $(Get-Date -Format o)"
Write-Host "Compose file: $composePath"
Write-Host "Drill DB: $drillDbName"

try {
    $backupScript = Join-Path $projectRoot "scripts\windows\backup_db.bat"
    if (-not (Test-Path $backupScript)) {
        throw "backup_db.bat not found at $backupScript"
    }

    Write-Host "==> Creating fresh backup"
    $env:LMS_COMPOSE_FILE = $composePath
    & $backupScript $backupDirPath
    if ($LASTEXITCODE -ne 0) {
        throw "backup_db.bat failed with exit code $LASTEXITCODE"
    }

    $backupFile = Get-ChildItem -Path $backupDirPath -Filter "lms_*.dump" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($null -eq $backupFile) {
        throw "No backup file found in $backupDirPath"
    }
    $backupFileName = $backupFile.Name
    Write-Host "Backup file: $($backupFile.FullName)"

    Write-Host "==> Creating drill database"
    $createDbCmd = "createdb -U `"`$POSTGRES_USER`" `"$drillDbName`""
    Invoke-Compose -Args @("exec", "-T", "db", "sh", "-lc", $createDbCmd) | Out-Null

    Write-Host "==> Copying backup into db container"
    Invoke-Compose -Args @("cp", $backupFile.FullName, "db:/tmp/$backupFileName") | Out-Null

    Write-Host "==> Restoring backup into drill database"
    $restoreCmd = "pg_restore -U `"`$POSTGRES_USER`" -d `"$drillDbName`" --clean --if-exists --no-owner --no-privileges /tmp/$backupFileName"
    Invoke-Compose -Args @("exec", "-T", "db", "sh", "-lc", $restoreCmd) | Out-Null

    Write-Host "==> Running restore validation checks"
    $tableCountCmd = "psql -U `"`$POSTGRES_USER`" -d `"$drillDbName`" -tAc `"SELECT count(*) FROM information_schema.tables WHERE table_schema='public';`""
    $tableCountLines = Invoke-Compose -Args @("exec", "-T", "db", "sh", "-lc", $tableCountCmd) -CaptureOutput
    $tableCountRaw = ($tableCountLines | Select-Object -Last 1).ToString().Trim()
    $tableCount = 0
    if (-not [int]::TryParse($tableCountRaw, [ref]$tableCount)) {
        throw "Failed to parse table count from restore validation output: '$tableCountRaw'"
    }

    if ($tableCount -lt $MinExpectedTables) {
        throw "Restore validation failed: expected at least $MinExpectedTables tables, got $tableCount"
    }

    Write-Host "Restore validation passed. Table count: $tableCount"
    Write-Host "==> Restore drill completed successfully"
}
finally {
    Remove-Item Env:LMS_COMPOSE_FILE -ErrorAction SilentlyContinue

    if ($backupFileName) {
        $cleanupDumpCmd = "rm -f /tmp/$backupFileName"
        try {
            Invoke-Compose -Args @("exec", "-T", "db", "sh", "-lc", $cleanupDumpCmd) | Out-Null
        }
        catch {
            Write-Warning "Failed to cleanup temporary dump in container: $($_.Exception.Message)"
        }
    }

    if (-not $KeepDrillDatabase) {
        $dropDbCmd = "dropdb -U `"`$POSTGRES_USER`" --if-exists `"$drillDbName`""
        try {
            Invoke-Compose -Args @("exec", "-T", "db", "sh", "-lc", $dropDbCmd) | Out-Null
        }
        catch {
            Write-Warning "Failed to drop drill database '$drillDbName': $($_.Exception.Message)"
        }
    }
    else {
        Write-Warning "KeepDrillDatabase is enabled. Database kept: $drillDbName"
    }

    Write-Host "Log file: $logFile"
    Stop-Transcript | Out-Null
}

