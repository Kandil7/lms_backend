# Staging Release Checklist

## 1. Deploy to Staging
1. Copy env:
```bash
cp .env.staging.example .env
```
2. Deploy:
```bash
docker compose -f docker-compose.staging.yml up -d --build
```
3. Run migrations:
```bash
docker compose -f docker-compose.staging.yml exec -T api alembic upgrade head
```

## 2. Validate Core Health
- `GET /api/v1/ready` returns `200`
- `GET /metrics` returns `200`
- `GET /docs` available in staging
- Sentry event appears in staging project (manual test exception)
- Grafana dashboard is receiving metrics

## 3. Validate Demo Flow
1. Run `run_demo.bat -NoBuild` in non-production environment.
2. Import `postman/LMS Backend Demo.postman_collection.json`.
3. Execute `Demo Quickstart` folder end-to-end.

## 4. Validate Load Baseline
```bat
run_load_test.bat http://localhost:8001 20 60s
```
Pass criteria:
- `http_req_failed < 1%`
- `p95 < 500ms`

Optional authenticated benchmark:
```bat
run_load_test.bat http://localhost:8001 20 60s localhost true
```

Realistic capacity benchmark:
```bat
run_load_test_realistic.bat http://localhost:8001 10m localhost 8 3 1
```

## 5. Validate Security and CI
- `ci.yml` green on branch.
- `security.yml` green on branch.
- secret scan (gitleaks) shows no leaks.

## 6. UAT / Bug Bash Pre-GoLive
- Execute plan in `docs/ops/04-uat-and-bug-bash-plan.md`.
- Fill templates in `docs/templates/`.
- Confirm no open `P0/P1` issues.

## 7. Go/No-Go
- If all checks pass: approve production deployment.
- If any check fails: open blocking incident and rollback to last green build.
