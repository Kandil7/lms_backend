# SLA, SLO, Incident, and Support Policy

## 1. Service Objectives

### SLA (external commitment)
- Monthly availability target: `99.5%`.
- Planned maintenance excluded with prior communication.

### SLO (internal target)
- API availability: `99.9%` monthly.
- p95 latency for critical APIs: `< 800ms`.
- Error budget policy:
  - If monthly error budget burn > 50% in first half of month, freeze non-critical releases.

## 2. Incident Severity
- `SEV-1`: complete outage or data loss risk.
- `SEV-2`: major feature degraded for many users.
- `SEV-3`: partial degradation with workaround.
- `SEV-4`: minor issue/no major user impact.

## 3. Incident Response Workflow
1. Detect: alert from Prometheus/Alertmanager/Sentry.
2. Acknowledge: on-call engineer within 10 minutes.
3. Triage: assign severity and incident commander.
4. Mitigate: rollback or hotfix.
5. Communicate: status updates on fixed cadence.
6. Resolve and close.
7. Postmortem within 48 hours for SEV-1/SEV-2.

## 4. Support Workflow
- Channels:
  - L1 support queue (customer-facing)
  - L2 engineering escalation
- Response targets:
  - SEV-1: 15 minutes
  - SEV-2: 1 hour
  - SEV-3: 4 hours
  - SEV-4: next business day

## 5. Status Communication Policy
- Internal channel update cadence:
  - SEV-1: every 30 minutes
  - SEV-2: every 60 minutes
- External status page update cadence:
  - initial post within 30 minutes of confirmation
  - updates every 60 minutes until resolved
- Mandatory fields per update:
  - incident ID
  - current impact
  - actions in progress
  - next update time

## 6. Runbook References
- Production runbook: `docs/ops/01-production-runbook.md`
- Launch tracker: `docs/ops/03-launch-readiness-tracker.md`
- Observability guide: `docs/ops/05-observability-and-alerting.md`

