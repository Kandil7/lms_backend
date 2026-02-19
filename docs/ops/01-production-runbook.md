# Production Runbook

## 1. Start and Validate
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
curl -f http://localhost:8000/api/v1/ready
```
4. Verify metrics endpoint:
```bash
curl -f http://localhost:8000/metrics
```

## 1.1 Staging Rehearsal
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
- Windows:
```bat
backup_db.bat
```
- Output path (default): `backups/db/lms_YYYYMMDD_HHMMSS.dump`
- Optional daily schedule (Windows):
```powershell
.\scripts\setup_backup_task.ps1 -TaskName LMS-DB-Backup -Time 02:00
```

## 4. Restore
- Windows:
```bat
restore_db.bat backups\db\lms_YYYYMMDD_HHMMSS.dump --yes
```

## 4.1 Restore Drill
- Manual:
```bat
restore_drill.bat -ComposeFile docker-compose.prod.yml
```
- Weekly scheduler:
```powershell
.\scripts\setup_restore_drill_task.ps1 -TaskName LMS-DB-Restore-Drill -Time 03:30 -DaysOfWeek Sunday -ComposeFile docker-compose.prod.yml
```

## 5. Logs and Troubleshooting
```bash
docker compose -f docker-compose.prod.yml logs --tail=200 api
docker compose -f docker-compose.prod.yml logs --tail=200 celery-worker
docker compose -f docker-compose.prod.yml logs --tail=200 celery-beat
docker compose -f docker-compose.observability.yml logs --tail=200 prometheus
docker compose -f docker-compose.observability.yml logs --tail=200 grafana
docker compose -f docker-compose.observability.yml logs --tail=200 alertmanager
```

## 6. Rollback
1. Stop current release.
2. Deploy previous image tag.
3. If schema rollback is needed, run the corresponding Alembic downgrade.
4. Restore latest known-good backup if data integrity is affected.

## 7. Security Notes
- Keep `ENABLE_API_DOCS=false` in production.
- Keep `STRICT_ROUTER_IMPORTS=true` in production.
- Keep `TASKS_FORCE_INLINE=false` in production.
- Rotate credentials regularly (`SECRET_KEY`, DB, SMTP).
- Review results of `.github/workflows/security.yml` on every PR.
- Configure `SENTRY_DSN` for API/Celery error tracking.
- Keep production secrets in Vault/Secret Manager, not `.env` in git.

## 8. Incident References
- Policy and severity model: `docs/ops/09-sla-slo-incident-support-policy.md`
- Observability setup: `docs/ops/05-observability-and-alerting.md`
