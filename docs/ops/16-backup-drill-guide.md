# Backup and Disaster Recovery Guide

This document outlines the backup and disaster recovery strategy for the LMS backend in production environments.

## 1. Overview

The LMS backend uses a comprehensive backup and recovery strategy with:
- **Daily backups**: Automated database dumps
- **Weekly restore drills**: Automated validation of backup integrity
- **Disaster recovery**: Comprehensive procedure for full system restoration

## 2. Backup Strategy

### 2.1 Backup Types
- **Full database backups**: Daily PostgreSQL dumps (compressed format)
- **Incremental backups**: Not currently implemented (recommended for large databases)
- **Configuration backups**: Manual backup of critical configuration files

### 2.2 Backup Schedule
- **Daily**: 2:00 AM local time (configurable via Windows Task Scheduler)
- **Retention**: 30 days minimum
- **Storage**: Local disk + offsite backup (to be configured)

### 2.3 Backup Format
- PostgreSQL custom format (`-Fc`) for efficient restoration
- Compressed with gzip (optional - not currently implemented)
- Timestamped filenames: `lms_YYYYMMDD_HHmmss.dump`

## 3. Current Backup Infrastructure

### 3.1 Scripts Overview
- `backup_db.bat`: Main backup script
- `restore_db.bat`: Restore script with safety checks
- `restore_drill.bat`: Automated restore drill execution
- `scripts/restore_drill.ps1`: PowerShell implementation of restore drill

### 3.2 Key Features
- **Safety checks**: Prevent accidental overwrites
- **Timestamp generation**: Automatic backup naming
- **Error handling**: Robust error detection and cleanup
- **Compose file flexibility**: Support for different environments

## 4. Production Backup Requirements

### 4.1 Essential Enhancements
- **Offsite backup storage**: Configure Azure Blob/GCS storage
- **Encryption**: Encrypt backup files at rest
- **Verification**: Add checksum verification
- **Monitoring**: Alert on backup failures

### 4.2 Recommended Configuration
```bat
:: Enhanced backup with encryption and offsite storage
@echo off
setlocal

call "%~dp0scripts\backup_db.bat" %*
if errorlevel 1 exit /b %errorlevel%

:: Encrypt backup
openssl enc -aes-256-cbc -salt -in "%BACKUP_FILE%" -out "%BACKUP_FILE%.enc" -pass pass:%ENCRYPTION_KEY%

:: Upload to Azure Blob
az storage blob upload ^
  --account-name %AZURE_STORAGE_ACCOUNT_NAME% ^
  --container-name lms-backups ^
  --name "prod/%DATE%/%~nxBACKUP_FILE%.enc" ^
  --file "%BACKUP_FILE%.enc" ^
  --auth-mode key

:: Verify upload
az storage blob list ^
  --account-name %AZURE_STORAGE_ACCOUNT_NAME% ^
  --container-name lms-backups ^
  --prefix "prod/%DATE%/" ^
  --auth-mode key
```

## 5. Restore Drill Procedure

### 5.1 Weekly Restore Drills
The automated restore drill performs:
1. Create temporary database instance
2. Restore from latest backup
3. Verify table count and data integrity
4. Run basic health checks
5. Clean up temporary resources

### 5.2 Drill Configuration
- **Frequency**: Weekly (Sundays at 3:30 AM)
- **Target**: Production-like environment
- **Validation**: Minimum 8 tables expected (core LMS tables)
- **Logging**: Detailed logs in `backups/drill_logs/`

### 5.3 Manual Drill Execution
```bash
# Run restore drill manually
.\restore_drill.bat -ComposeFile docker-compose.prod.yml

# Run with specific backup
.\restore_drill.bat -ComposeFile docker-compose.prod.yml -BackupFile backups\db\lms_20240115_020000.dump
```

## 6. Disaster Recovery Plan

### 6.1 RTO/RPO Objectives
- **Recovery Time Objective (RTO)**: 4 hours maximum
- **Recovery Point Objective (RPO)**: 24 hours maximum
- **Critical systems**: Database, Redis, file storage

### 6.2 DR Scenarios and Procedures

#### Scenario 1: Database Corruption
1. Stop application services
2. Restore from latest backup using `restore_db.bat`
3. Verify data integrity
4. Restart services
5. Run post-recovery validation

#### Scenario 2: Complete Infrastructure Failure
1. Provision new infrastructure
2. Restore database from offsite backup
3. Restore file storage from backup
4. Deploy application code
5. Configure environment variables and secrets
6. Run full validation suite

#### Scenario 3: Data Loss (Accidental Deletion)
1. Identify affected data and timestamp
2. Restore from backup at appropriate point-in-time
3. Extract and merge affected records
4. Validate data consistency
5. Notify stakeholders

## 7. Verification and Testing

### 7.1 Backup Verification Checklist
- [ ] Daily backup completes successfully
- [ ] Backup file size is reasonable (not zero bytes)
- [ ] Backup contains expected tables and data
- [ ] Restore works without errors
- [ ] Drill runs successfully weekly

### 7.2 Automated Validation
Add to CI/CD pipeline:
```yaml
# GitHub Actions example
- name: Verify backup integrity
  run: |
    ./scripts/backup_db.bat
    ./scripts/restore_drill.bat -ComposeFile docker-compose.test.yml
```

## 8. Monitoring and Alerting

### 8.1 Backup Alerts
- **Critical**: Backup failure
- **Warning**: Backup size异常 (too small/large)
- **Info**: Backup completed successfully

### 8.2 DR Readiness Metrics
- Backup success rate (target: 100%)
- Restore drill success rate (target: 100%)
- RTO/RPO compliance (target: within objectives)
- Backup retention compliance (target: 100%)

## 9. Documentation Requirements

- Backup schedule and retention policy
- DR runbook with step-by-step procedures
- Contact list for incident response
- Regular DR testing schedule
- Post-incident review procedures

## 10. Security Considerations

### 10.1 Backup Security
- Encrypt backup files at rest
- Restrict access to backup storage
- Use secure transfer protocols
- Audit backup access logs

### 10.2 Compliance Requirements
- GDPR: Right to be forgotten for backup data
- HIPAA: If handling health data
- PCI-DSS: If handling payment information
- SOC 2: Backup and recovery requirements

## 11. Implementation Steps

### 11.1 Immediate Actions
1. Configure offsite backup storage
2. Implement backup encryption
3. Set up monitoring and alerts
4. Document DR procedures

### 11.2 Ongoing Maintenance
1. Weekly restore drills (already automated)
2. Monthly DR testing
3. Quarterly review of backup policies
4. Annual full DR simulation

## 12. Troubleshooting

### Common Issues:
- **Backup fails**: Check database connectivity and permissions
- **Restore fails**: Verify backup file integrity and PostgreSQL version compatibility
- **Drill fails**: Check temporary database creation and network connectivity
- **High backup size**: Review data growth and consider archiving

### Debugging Commands:
```bash
# Test backup creation
.\backup_db.bat

# Test restore with dry-run
.\restore_db.bat backups\db\lms_20240115_020000.dump --dry-run

# Check backup integrity
pg_restore -l backups\db\lms_20240115_020000.dump | head -20
```
