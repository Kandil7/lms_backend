# Production Runbook

Current scope note:
- The payments module is deferred in the current backend release scope.
- Payment-specific checklist items are only required when payments are explicitly reactivated.

## 0. Go-Live Checklist
Use this checklist before approving production release.  
Status values:
- `Done`: `Yes` or `No`
- `Owner`: team/person responsible
- `Date`: target or completion date (`YYYY-MM-DD`)
- `Evidence`: link to PR, CI run, dashboard screenshot, or ticket

| Item | Done | Owner | Date | Evidence |
|---|---|---|---|---|
| Release commit + tag created from tested branch | No |  |  |  |
| CI green (tests + security workflow) | No |  |  |  |
| Alembic migration applied on staging and production | No |  |  |  |
| Payments module activated for this release | No |  |  |  |
| MyFatoorah live credentials configured in secret manager (only if payments active) | No |  |  |  |
| `MYFATOORAH_WEBHOOK_SECRET` configured and verified (only if payments active) | No |  |  |  |
| MyFatoorah webhook endpoint reachable: `/api/v1/payments/webhooks/myfatoorah` (only if payments active) | No |  |  |  |
| Payment E2E tested (success, failed, refunded, duplicate webhook) (only if payments active) | No |  |  |  |
| SMTP production config validated (send/receive) | No |  |  |  |
| Backup task running daily with successful latest run | No |  |  |  |
| Restore drill executed and validated | No |  |  |  |
| Observability live (Grafana/Alertmanager/Sentry) with active alerts | No |  |  |  |
| Production-like smoke check passed (`run_load_test.bat`) | No |  |  |  |
| Security hardening sign-off (CSP, sanitization, secrets policy) | No |  |  |  |
| SLA/SLO + incident response workflow approved | No |  |  |  |
| Legal docs approved (Privacy, Terms, retention/deletion policy) | No |  |  |  |

Go/No-Go Rule:
1. Launch only when all critical items above are `Done=Yes`.
2. If any critical item is `No`, release is blocked.

## 1. Start and Validate
Pre-requisites in `.env`:
- `PROD_DATABASE_URL` points to Azure Database for PostgreSQL Flexible Server with `sslmode=require`
- `APP_DOMAIN` points to your production DNS record
- `LETSENCRYPT_EMAIL` is a valid ops email for ACME/TLS issuance

1. Start stack:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
2. Start observability stack:
```bash
docker compose -f docker-compose.observability.yml up -d
```
3. Verify readiness:
```bash
curl -f https://<APP_DOMAIN>/api/v1/ready
```
4. Verify metrics endpoint:
```bash
curl -f https://<APP_DOMAIN>/metrics
```
5. Run production-like smoke checks:
```bat
run_load_test.bat https://<APP_DOMAIN> 20 60s
```

### 1.1 Staging Rehearsal
1. Start staging stack:
```bash
docker compose -f docker-compose.staging.yml up -d --build
```
2. Verify staging readiness:
```bash
curl -f http://localhost:8001/api/v1/ready
```
3. Run smoke load test:
```bat
run_load_test.bat http://localhost:8001 20 60s
```

## 2. Health Checks
- API readiness: `GET /api/v1/ready`
- Liveness: `GET /api/v1/health`
- Metrics: `GET /metrics`

## 3. Backup
- Use Azure Database for PostgreSQL built-in backups (PITR retention configured on server).
- Validate latest recovery point in Azure Portal before each release.

## 4. Restore
- Perform restore using Azure PostgreSQL point-in-time restore or server restore workflow.
- For app rollback, redeploy previous app commit and keep DB restore isolated to incidents requiring data recovery.

### 4.1 Restore Drill
- Manual:
```bat
restore_drill.bat -ComposeFile docker-compose.prod.yml
```
- Weekly scheduler:
```powershell
.\scripts\setup_restore_drill_task.ps1 -TaskName LMS-DB-Restore-Drill -Time 03:30 -DaysOfWeek Sunday -ComposeFile docker-compose.prod.yml
```

## 5. Routine Operations

### 5.1 Daily Operations
#### Backup Verification
```bash
# Verify daily backup completed successfully
.\backup_db.bat
# Check backup file size and timestamp
dir backups\db\*.dump | findstr "lms_"
```

#### System Health Check
```bash
# API health check
curl -I http://localhost:8000/api/v1/health

# Database health
docker compose exec db psql -U lms -d lms -c "SELECT 1;"

# Redis health
docker compose exec redis redis-cli ping

# Celery workers
docker compose exec celery-worker celery -A app.tasks.celery_app.celery_app inspect ping
```

#### Monitoring Review
- **Grafana dashboards**: Review key metrics (CPU, memory, latency, errors)
- **Sentry issues**: Review new issues and alerts
- **Log analysis**: Check for error patterns and security events
- **Backup status**: Verify backup completion and integrity

### 5.2 Weekly Operations
#### Restore Drill Execution
```bash
# Run weekly restore drill
.\restore_drill.bat -ComposeFile docker-compose.prod.yml
# Verify drill logs
type backups\drill_logs\*.log | findstr "SUCCESS"
```

#### Performance Review
- Review k6 load test results from previous week
- Analyze SLO compliance reports
- Identify performance trends and optimization opportunities
- Update capacity planning based on usage patterns

#### Security Review
- Review security scan results (bandit, pip-audit)
- Check for new vulnerabilities in dependencies
- Review access logs for suspicious activity
- Verify backup encryption and security controls

### 5.3 Monthly Operations
#### Capacity Planning
- Review resource utilization trends
- Plan infrastructure scaling if needed
- Update backup retention policies
- Review and update disaster recovery procedures

#### Compliance Review
- Verify data retention policy compliance
- Review privacy policy and terms of service
- Update incident response procedures
- Conduct staff training on operational procedures

## 6. Logs and Troubleshooting
```bash
docker compose -f docker-compose.prod.yml logs --tail=200 api
docker compose -f docker-compose.prod.yml logs --tail=200 celery-worker
docker compose -f docker-compose.prod.yml logs --tail=200 celery-beat
docker compose -f docker-compose.observability.yml logs --tail=200 prometheus
docker compose -f docker-compose.observability.yml logs --tail=200 grafana
docker compose -f docker-compose.observability.yml logs --tail=200 alertmanager
```

Flower quick check:
```bash
curl -I http://localhost:5555
```

## 7. Incident Response

### 7.1 Critical Incidents (P1)
#### API Unavailability
**Symptoms**: 500 errors, timeout errors, service unreachable
**Immediate Actions**:
1. Verify monitoring alerts and confirm outage
2. Check application logs: `docker logs api`
3. Check database connectivity: `docker compose exec db psql -U lms -d lms -c "SELECT 1;"`
4. Check Redis connectivity: `docker compose exec redis redis-cli ping`
5. Restart API service: `docker compose restart api`
6. If issue persists, roll back to previous version
7. Notify stakeholders and update status page

**Root Cause Analysis**:
- Database connection pool exhaustion
- Memory leaks in application
- Network connectivity issues
- External service failures

#### Database Failure
**Symptoms**: Database connection errors, slow queries, high CPU
**Immediate Actions**:
1. Verify database health: `docker compose exec db pg_isready -U lms -d lms`
2. Check PostgreSQL logs: `docker logs db`
3. Monitor resource usage: `docker stats db`
4. If database is unresponsive, restart: `docker compose restart db`
5. Restore from latest backup if corruption detected
6. Implement temporary read-only mode if needed

### 7.2 High Severity Incidents (P2)
#### Authentication Issues
**Symptoms**: Login failures, token validation errors, MFA problems
**Actions**:
1. Check authentication service logs
2. Verify Redis connectivity (for rate limiting and session storage)
3. Test with known good credentials
4. Check JWT secret rotation status
5. Temporarily disable rate limiting for investigation
6. Roll back recent auth changes if needed

#### File Storage Issues
**Symptoms**: Upload/download failures, file not found errors
**Actions**:
1. Verify uploads directory permissions
2. Check disk space: `df -h`
3. Test file system operations locally
4. Verify S3 connectivity (if using S3)
5. Check Redis cache for file metadata
6. Restore from backup if data corruption suspected

## 8. Maintenance Procedures

### 8.1 Software Updates
#### Application Updates
1. **Pre-update checklist**:
   - Verify backup completed
   - Confirm staging environment matches production
   - Review release notes and breaking changes
   - Prepare rollback plan

2. **Update procedure**:
   ```bash
   # Build new image
   docker build -t lms-api:latest .
   
   # Test in staging
   docker compose -f docker-compose.staging.yml up --build
   
   # Deploy to production
   docker compose -f docker-compose.prod.yml up --build --detach
   
   # Monitor for 15 minutes
   curl -I http://localhost:8000/api/v1/health
   ```

3. **Post-update verification**:
   - Run smoke tests
   - Verify key business flows
   - Monitor error rates and latency
   - Confirm backup runs successfully

### 8.2 Database Maintenance
#### Schema Migrations
1. **Pre-migration checklist**:
   - Backup database
   - Verify migration scripts
   - Test migration in staging
   - Prepare rollback script

2. **Migration procedure**:
   ```bash
   # Apply migration
   docker compose exec api alembic upgrade head
   
   # Verify migration
   docker compose exec api python -c "from app.modules.courses.models import Course; print(Course.__tablename__)"
   
   # Monitor for errors
   docker logs api | grep -i "error"
   ```

3. **Rollback procedure**:
   ```bash
   # Rollback to previous revision
   docker compose exec api alembic downgrade -1
   
   # Verify data integrity
   docker compose exec api python -c "from app.modules.enrollments.models import Enrollment; print(Enrollment.query.count())"
   ```

### 8.3 Infrastructure Scaling
#### Horizontal Scaling (API Instances)
1. **Scale up**:
   ```bash
   # Update docker-compose.prod.yml
   # services:
   #   api:
   #     deploy:
   #       replicas: 4
   
   # Apply scaling
   docker compose -f docker-compose.prod.yml up --scale api=4
   ```

2. **Scale down**: Reverse the process

3. **Load balancing**: Ensure reverse proxy is configured for multiple instances

#### Vertical Scaling (Resource Allocation)
1. **Increase resources**:
   - Update Docker Compose resource limits
   - Increase PostgreSQL shared_buffers and work_mem
   - Adjust Redis maxmemory settings
   - Optimize connection pools

2. **Monitor impact**: Track performance metrics after scaling

## 9. Security Operations

### 9.1 Secret Rotation
#### Application Secrets
1. **Generate new secrets**:
   ```bash
   # Generate new SECRET_KEY
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Update secrets in Vault**:
   ```
   vault kv put secret/data/lms/SECRET_KEY value=new-secret-value
   ```

3. **Restart services**: `docker compose restart api celery-worker`

4. **Verify operation**: Test critical functionality

### 9.2 Certificate Management
#### TLS Certificate Renewal
1. **Check expiration**:
   ```bash
   openssl x509 -in /path/to/cert.pem -noout -dates
   ```

2. **Renew certificate**: Use Let's Encrypt or CA renewal process

3. **Update reverse proxy**: Replace certificate files
4. **Restart services**: `docker compose restart nginx` (or equivalent)

## 10. Disaster Recovery Procedures

### 10.1 Full System Restoration
**Scenario**: Complete infrastructure failure

1. **Provision new infrastructure**
2. **Restore database**:
   ```bash
   .\restore_db.bat backups\db\lms_20240115_020000.dump --yes
   ```

3. **Restore file storage**: Copy uploads and certificates from backup
4. **Deploy application code**: Git clone and build
5. **Configure environment**: Set up .env files and secrets
6. **Start services**: `docker compose -f docker-compose.prod.yml up -d`
7. **Run validation suite**: Comprehensive health checks

### 10.2 Partial Data Recovery
**Scenario**: Specific data loss (e.g., course deletion)

1. **Identify affected data**: Determine what was lost and when
2. **Restore from backup**: Extract specific records from backup
3. **Merge data**: Carefully merge restored data with current data
4. **Validate integrity**: Verify data consistency and relationships
5. **Notify users**: Communicate recovery actions

## 11. Rollback
1. Stop current release.
2. Deploy previous image tag.
3. If schema rollback is needed, run the corresponding Alembic downgrade.
4. Restore latest known-good backup if data integrity is affected.

## 12. Security Notes
- Keep `ENABLE_API_DOCS=false` in production.
- Keep `STRICT_ROUTER_IMPORTS=true` in production.
- Keep `TASKS_FORCE_INLINE=false` in production.
- If the deferred payments module is reactivated, keep payment sandbox/mock mode disabled in production.
- Rotate credentials regularly (`SECRET_KEY`, DB, SMTP).
- Review results of `.github/workflows/security.yml` on every PR.
- Configure `SENTRY_DSN` for API/Celery error tracking.
- Keep production secrets in Vault/Secret Manager, not `.env` in git.

## 13. Incident References
- Policy and severity model: `docs/ops/09-sla-slo-incident-support-policy.md`
- Observability setup: `docs/ops/05-observability-and-alerting.md`
- Comprehensive observability guide: `docs/ops/13-observability-guide.md`

## 14. Essential Commands Reference
```bash
# System monitoring
docker stats --no-stream

# Log analysis
docker logs api | grep -i "error"

# Database diagnostics
docker compose exec db psql -U lms -d lms -c "SELECT 1;"
redis-cli info memory

# Celery
celery -A app.tasks.celery_app.celery_app inspect stats
celery -A app.tasks.celery_app.celery_app inspect ping
```

## 15. Operational Checklists

### Pre-Launch Checklist
- [ ] All systems operational
- [ ] Backup verified and tested
- [ ] Monitoring and alerting enabled
- [ ] UAT sign-off obtained
- [ ] Legal compliance review completed
- [ ] Documentation published
- [ ] Support team trained
- [ ] On-call schedule established

### Post-Incident Checklist
- [ ] Root cause identified
- [ ] Fix implemented and tested
- [ ] Prevention measures deployed
- [ ] Documentation updated
- [ ] Team debrief conducted
- [ ] Metrics reviewed and updated
