# Launch Readiness Tracker

Use this tracker as the release gate before production go-live.

## 1. UAT and Bug Bash
- Owner: Product + QA
- Target status: `Done before launch week`
- Evidence required:
  - UAT sign-off report with real pilot users
  - Bug bash report with triage decisions
- Artifacts:
  - `docs/ops/04-uat-and-bug-bash-plan.md`
  - `docs/templates/uat-scenario-template.md`
  - `docs/templates/bug-bash-report-template.md`

## 2. Observability Operational Readiness
- Owner: Backend + DevOps
- Target status: `Enabled on staging and production`
- Evidence required:
  - Grafana dashboard screenshots
  - Alert test event delivered to incident channel
  - Sentry issue generated and acknowledged
- Artifacts:
  - `docker-compose.observability.yml`
  - `ops/observability/prometheus/alerts.yml`
  - `docs/ops/05-observability-and-alerting.md`

## 3. Backup and Restore Drill
- Owner: DevOps
- Target status: `Daily backup + weekly drill`
- Evidence required:
  - Backup task exists and last run is successful
  - Restore drill logs for last 4 weeks
- Artifacts:
  - `backup_db.bat`
  - `restore_drill.bat`
  - `scripts/setup_backup_task.ps1`
  - `scripts/setup_restore_drill_task.ps1`
  - `docs/ops/06-backup-and-restore-drill-policy.md`

## 4. Security Sign-off
- Owner: Security + Backend
- Target status: `Clean security workflow on release commit`
- Evidence required:
  - `security.yml` green on release branch
  - Secret management path documented and validated
  - Server hardening checklist completed
- Artifacts:
  - `.github/workflows/security.yml`
  - `docs/ops/07-security-signoff-and-hardening.md`

## 5. Load and Capacity Sign-off
- Owner: Backend + QA
- Target status: `Capacity baseline approved`
- Evidence required:
  - Realistic k6 report for staging/prod-like env
  - Capacity estimate (peak RPS, safe concurrent users)
  - Remediation plan for bottlenecks
- Artifacts:
  - `tests/perf/k6_realistic.js`
  - `run_load_test_realistic.bat`
  - `docs/ops/08-performance-capacity-signoff.md`

## 6. Service Operations Policy
- Owner: Product + Support + Engineering
- Target status: `Published internally`
- Evidence required:
  - SLA/SLO baselines approved
  - Incident response roles confirmed
  - Support and status communication workflow active
- Artifact:
  - `docs/ops/09-sla-slo-incident-support-policy.md`

## 7. Legal and Compliance
- Owner: Product + Legal
- Target status: `Published before launch`
- Evidence required:
  - Privacy Policy published
  - Terms of Service published
  - Data retention and deletion policy approved
- Artifacts:
  - `docs/legal/privacy-policy-template.md`
  - `docs/legal/terms-of-service-template.md`
  - `docs/legal/data-retention-and-deletion-policy.md`

