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
  - Secret management implementation validated (Vault integration)
  - TLS termination with modern ciphers and HSTS configured
  - Server hardening checklist completed and verified
- Artifacts:
  - `.github/workflows/security.yml`
  - `docs/ops/07-security-signoff-and-hardening.md`
  - `docs/ops/10-secrets-management-guide.md`
  - `docs/ops/11-tls-termination-guide.md`
  - `docs/ops/12-server-hardening-guide.md`

## 5. Observability Operational Readiness
- Owner: Backend + DevOps
- Target status: `Enabled on staging and production`
- Evidence required:
  - Grafana dashboards customized for LMS metrics
  - Alert test event delivered to incident channel
  - Sentry issue generated and acknowledged
  - Sentry configuration verified with proper DSN and environment settings
  - Log centralization implemented with retention policy
- Artifacts:
  - `docker-compose.observability.yml`
  - `ops/observability/prometheus/alerts.yml`
  - `docs/ops/05-observability-and-alerting.md`
  - `docs/ops/13-observability-guide.md`
  - `docs/ops/14-sentry-configuration-guide.md`
  - `docs/ops/15-logging-guide.md`

## 6. Backup and Disaster Recovery
- Owner: DevOps
- Target status: `Daily backup + weekly drill`
- Evidence required:
  - Backup task exists and last run is successful
  - Restore drill logs for last 4 weeks
  - DR procedure documented, tested, and validated
- Artifacts:
  - `backup_db.bat`
  - `restore_drill.bat`
  - `scripts/setup_backup_task.ps1`
  - `scripts/setup_restore_drill_task.ps1`
  - `docs/ops/06-backup-and-restore-drill-policy.md`
  - `docs/ops/16-backup-drill-guide.md`

## 7. Performance and Capacity Sign-off
- Owner: Backend + QA
- Target status: `Capacity baseline approved`
- Evidence required:
  - Realistic k6 report for staging/prod-like env
  - Capacity estimate (peak RPS, safe concurrent users)
  - Remediation plan for bottlenecks
  - Database optimization and indexing completed
  - Caching strategy implemented and validated
- Artifacts:
  - `tests/perf/k6_realistic.js`
  - `run_load_test_realistic.bat`
  - `docs/ops/08-performance-capacity-signoff.md`
  - `docs/ops/17-performance-optimization-guide.md`

## 8. Operational Readiness
- Owner: Product + Support + Engineering
- Target status: `Published internally`
- Evidence required:
  - UAT sign-off report with real pilot users
  - Bug bash report with triage decisions
  - SLA/SLO baselines approved and documented
  - Incident response roles confirmed
  - Support and status communication workflow active
- Artifacts:
  - `docs/ops/04-uat-and-bug-bash-plan.md`
  - `docs/templates/uat-scenario-template.md`
  - `docs/templates/bug-bash-report-template.md`
  - `docs/ops/09-sla-slo-incident-support-policy.md`
  - `docs/ops/19-uat-procedures-guide.md`
  - `docs/ops/20-sla-slo-baselines.md`

## 9. Testing and Documentation
- Owner: Engineering + QA
- Target status: `Quality gates met`
- Evidence required:
  - Test coverage ≥ 75% (current: 77%)
  - Critical test cases pass rate 100%
  - Operational runbooks completed and reviewed
  - Testing strategy documented and approved
- Artifacts:
  - `tests/` directory with comprehensive test suite
  - `docs/ops/21-testing-strategy.md`
  - `docs/ops/22-operational-runbooks.md`
  - CI/CD pipeline with quality gates

