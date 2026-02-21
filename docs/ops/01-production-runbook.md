# Production Runbook

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
| MyFatoorah live credentials configured in secret manager | No |  |  |  |
| `MYFATOORAH_WEBHOOK_SECRET` configured and verified | No |  |  |  |
| MyFatoorah webhook endpoint reachable: `/api/v1/payments/webhooks/myfatoorah` | No |  |  |  |
| Payment E2E tested (success, failed, refunded, duplicate webhook) | No |  |  |  |
| SMTP production config validated (send/receive) | No |  |  |  |
| Backup task running daily with successful latest run | No |  |  |  |
| Restore drill executed and validated | No |  |  |  |
| Observability live (Grafana/Alertmanager/Sentry) with active alerts | No |  |  |  |
| Production-like smoke check passed (`run_smoke_prod_like.bat`) | No |  |  |  |
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
run_smoke_prod_like.bat
```
Or:
```bash
python scripts/smoke_prod_like.py --base-url http://localhost:8000 --flower-url http://localhost:5555 --compose-file docker-compose.prod.yml
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
- Use Azure Database for PostgreSQL built-in backups (PITR retention configured on server).
- Validate latest recovery point in Azure Portal before each release.

## 4. Restore
- Perform restore using Azure PostgreSQL point-in-time restore or server restore workflow.
- For app rollback, redeploy previous app commit and keep DB restore isolated to incidents requiring data recovery.

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

Flower quick check:
```bash
curl -I http://localhost:5555
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
- Keep `PAYMENTS_MOCK_MODE=false` in production.
- Rotate credentials regularly (`SECRET_KEY`, DB, SMTP).
- Review results of `.github/workflows/security.yml` on every PR.
- Configure `SENTRY_DSN` for API/Celery error tracking.
- Keep production secrets in Vault/Secret Manager, not `.env` in git.

## 8. Incident References
- Policy and severity model: `docs/ops/09-sla-slo-incident-support-policy.md`
- Observability setup: `docs/ops/05-observability-and-alerting.md`
