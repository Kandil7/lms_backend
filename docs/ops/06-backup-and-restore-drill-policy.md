# Backup and Restore Drill Policy

## 1. Policy
- Database backups: daily at `02:00`.
- Restore drill: weekly at `03:30` (Sunday recommended).
- Recovery objective targets:
  - RPO <= 24h
  - RTO <= 60min

## 2. Automation Scripts
- Backup:
  - `backup_db.bat`
  - `scripts/setup_backup_task.ps1`
- Restore drill:
  - `restore_drill.bat`
  - `scripts/run_restore_drill.ps1`
  - `scripts/setup_restore_drill_task.ps1`

## 3. Setup (Windows)
1. Daily backup task:
```powershell
.\scripts\setup_backup_task.ps1 -TaskName LMS-DB-Backup -Time 02:00
```
2. Weekly restore drill task:
```powershell
.\scripts\setup_restore_drill_task.ps1 -TaskName LMS-DB-Restore-Drill -Time 03:30 -DaysOfWeek Sunday -ComposeFile docker-compose.prod.yml
```

## 4. Manual Drill Command
```bat
restore_drill.bat -ComposeFile docker-compose.prod.yml
```

## 5. Evidence Retention
- Keep drill logs under:
  - `backups/drill_logs/`
- Keep database dumps under:
  - `backups/db/`
- Retention recommendation:
  - backups: 30 days
  - drill logs: 90 days

## 6. Acceptance Criteria Per Drill
- Backup created successfully.
- Temporary restore DB created and restored successfully.
- Validation query passed (expected public table count).
- Drill database dropped after validation.
- Log stored with timestamp.

