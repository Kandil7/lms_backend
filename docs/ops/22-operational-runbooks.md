# Operational Runbooks

This document provides comprehensive operational runbooks for the LMS backend in production environments.

## 1. Overview

Operational runbooks are step-by-step procedures for routine operations, incident response, and system maintenance. These runbooks ensure consistent operations and rapid incident resolution.

## 2. Routine Operations

### 2.1 Daily Operations
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

### 2.2 Weekly Operations
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

### 2.3 Monthly Operations
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

## 3. Incident Response Runbooks

### 3.1 Critical Incidents (P1)
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

### 3.2 High Severity Incidents (P2)
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

## 4. Maintenance Procedures

### 4.1 Software Updates
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

### 4.2 Database Maintenance
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

### 4.3 Infrastructure Scaling
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

## 5. Security Operations

### 5.1 Secret Rotation
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

### 5.2 Certificate Management
#### TLS Certificate Renewal
1. **Check expiration**:
   ```bash
   openssl x509 -in /path/to/cert.pem -noout -dates
   ```

2. **Renew certificate**: Use Let's Encrypt or CA renewal process

3. **Update reverse proxy**: Replace certificate files
4. **Restart services**: `docker compose restart nginx` (or equivalent)

## 6. Disaster Recovery Procedures

### 6.1 Full System Restoration
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

### 6.2 Partial Data Recovery
**Scenario**: Specific data loss (e.g., course deletion)

1. **Identify affected data**: Determine what was lost and when
2. **Restore from backup**: Extract specific records from backup
3. **Merge data**: Carefully merge restored data with current data
4. **Validate integrity**: Verify data consistency and relationships
5. **Notify users**: Communicate recovery actions

## 7. Operational Checklists

### 7.1 Pre-Launch Checklist
- [ ] All systems operational
- [ ] Backup verified and tested
- [ ] Monitoring and alerting enabled
- [ ] UAT sign-off obtained
- [ ] Legal compliance review completed
- [ ] Documentation published
- [ ] Support team trained
- [ ] On-call schedule established

### 7.2 Post-Incident Checklist
- [ ] Root cause identified
- [ ] Fix implemented and tested
- [ ] Prevention measures deployed
- [ ] Documentation updated
- [ ] Team debrief conducted
- [ ] Metrics reviewed and updated

## 8. Tools and References

### 8.1 Essential Commands
```bash
# System monitoring
docker stats --no-stream
kubectl get pods -n lms
ps aux | grep uvicorn

# Log analysis
docker logs api | grep -i "error"
grep "ERROR" logs/app.log
journalctl -u lms-api -f

# Database diagnostics
pg_top
redis-cli info memory
celery -A app.tasks.celery_app.celery_app inspect stats
```

### 8.2 Reference Documents
- `docs/ops/03-launch-readiness-tracker.md`
- `docs/ops/05-observability-and-alerting.md`
- `docs/ops/07-security-signoff-and-hardening.md`
- `docs/ops/09-sla-slo-incident-support-policy.md`
- `docs/ops/13-observability-guide.md`
- `docs/ops/14-sentry-configuration-guide.md`

## 9. Version Control and Updates

### 9.1 Runbook Maintenance
- **Review frequency**: Quarterly
- **Update triggers**: 
  - Major system changes
  - New security vulnerabilities
  - Process improvements
  - Incident learnings
- **Approval process**: Engineering lead + Product manager

### 9.2 Change Log
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-01-15 | 1.0 | Initial runbook creation | Operations Team |
| 2024-02-01 | 1.1 | Added incident response procedures | Security Team |
| 2024-02-15 | 1.2 | Updated backup and DR procedures | DevOps Team |

## 10. Training and Knowledge Transfer

### 10.1 New Team Member Onboarding
1. **Week 1**: Study runbooks and documentation
2. **Week 2**: Shadow operations team
3. **Week 3**: Perform supervised operations
4. **Week 4**: Handle minor incidents independently

### 10.2 Cross-Training Requirements
- All engineers must be able to perform basic incident response
- At least 2 people per critical function
- Regular knowledge sharing sessions
- Documentation contribution requirements

This operational runbook provides comprehensive guidance for maintaining and operating the LMS backend in production environments.