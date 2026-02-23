# LMS Backend - Master Documentation Index

This is the comprehensive documentation index for the LMS Backend project. All documentation files are organized by category for easy navigation.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Main documentation index |
| [docs/tech/MASTER-COMPREHENSIVE-DOCUMENTATION.md](docs/tech/MASTER-COMPREHENSIVE-DOCUMENTATION.md) | Complete technical documentation |
| [docs/tech/18-Complete-Project-Summary.md](docs/tech/18-Complete-Project-Summary.md) | Quick reference summary |

---

## Documentation Structure

### 1. Root Documentation (docs/)

| File | Description |
|------|-------------|
| [README.md](README.md) | Main documentation index (this file) |
| [implementation_plan.md](implementation_plan.md) | Project implementation plan |
| [CLIENT_APP_IMPLEMENTATION_PLAN.md](CLIENT_APP_IMPLEMENTATION_PLAN.md) | Client app implementation plan |
| [08-api-documentation.md](08-api-documentation.md) | API documentation overview |
| [09-full-api-reference.md](09-full-api-reference.md) | Full API reference (generated from live schema) |

---

### 2. Technical Documentation (docs/tech/)

The tech folder contains comprehensive English technical documentation.

#### Core Complete Guides (Recommended)

| File | Description |
|------|-------------|
| [docs/tech/MASTER-COMPREHENSIVE-DOCUMENTATION.md](docs/tech/MASTER-COMPREHENSIVE-DOCUMENTATION.md) | Master index for all tech docs |
| [docs/tech/18-Complete-Project-Summary.md](docs/tech/18-Complete-Project-Summary.md) | Quick reference summary |
| [docs/tech/17-Complete-File-By-File-Documentation.md](docs/tech/17-Complete-File-By-File-Documentation.md) | Every file in the project |
| [docs/tech/04-Complete-Build-And-Run-Guide.md](docs/tech/04-Complete-Build-And-Run-Guide.md) | Build & run instructions |
| [docs/tech/02-Complete-Architecture-Decisions.md](docs/tech/02-Complete-Architecture-Decisions.md) | Why each decision was made |

#### API & Modules

| File | Description |
|------|-------------|
| [docs/tech/10-Complete-API-Routes-Reference.md](docs/tech/10-Complete-API-Routes-Reference.md) | Complete API endpoints |
| [docs/tech/09-Complete-Modules-Detailed.md](docs/tech/09-Complete-Modules-Detailed.md) | All modules explained |

#### Security & Operations

| File | Description |
|------|-------------|
| [docs/tech/06-Complete-Security-And-Authentication.md](docs/tech/06-Complete-Security-And-Authentication.md) | Security implementation |
| [docs/tech/12-Complete-Operations-Infrastructure.md](docs/tech/12-Complete-Operations-Infrastructure.md) | Operations & infrastructure |
| [docs/tech/11-Complete-Ops-Infrastructure-Config.md](docs/tech/11-Complete-Ops-Infrastructure-Config.md) | Ops configs (Caddy, Prometheus) |
| [docs/tech/13-Complete-Docker-Configuration.md](docs/tech/13-Complete-Docker-Configuration.md) | Docker configs |

#### Development & CI/CD

| File | Description |
|------|-------------|
| [docs/tech/07-Complete-Testing-Strategy.md](docs/tech/07-Complete-Testing-Strategy.md) | Testing strategy |
| [docs/tech/08-Complete-Background-Jobs-Celery.md](docs/tech/08-Complete-Background-Jobs-Celery.md) | Celery tasks |
| [docs/tech/14-Complete-Scripts-Reference.md](docs/tech/14-Complete-Scripts-Reference.md) | All scripts explained |
| [docs/tech/15-Complete-GitHub-Workflows.md](docs/tech/15-Complete-GitHub-Workflows.md) | CI/CD pipelines |

---

### 3. Operations Guides (docs/ops/)

| # | File | Description |
|---|------|-------------|
| 01 | [docs/ops/01-production-runbook.md](docs/ops/01-production-runbook.md) | Production runbook (comprehensive - includes routine ops, incident response, maintenance, DR) |
| 02 | [docs/ops/02-staging-release-checklist.md](docs/ops/02-staging-release-checklist.md) | Staging checklist |
| 03 | [docs/ops/03-launch-readiness-tracker.md](docs/ops/03-launch-readiness-tracker.md) | Launch readiness |
| 04 | [docs/ops/04-uat-and-bug-bash-plan.md](docs/ops/04-uat-and-bug-bash-plan.md) | UAT plan |
| 05 | [docs/ops/05-observability-and-alerting.md](docs/ops/05-observability-and-alerting.md) | Observability setup (quick reference - see #13 for detailed guide) |
| 06 | [docs/ops/06-backup-and-restore-drill-policy.md](docs/ops/06-backup-and-restore-drill-policy.md) | Backup policy |
| 07 | [docs/ops/07-security-signoff-and-hardening.md](docs/ops/07-security-signoff-and-hardening.md) | Security hardening (see #24 for secrets management) |
| 08 | [docs/ops/08-performance-capacity-signoff.md](docs/ops/08-performance-capacity-signoff.md) | Performance signoff |
| 09 | [docs/ops/09-sla-slo-incident-support-policy.md](docs/ops/09-sla-slo-incident-support-policy.md) | SLA/SLO policy |
| 10 | [docs/ops/10-azure-production-deployment.md](docs/ops/10-azure-production-deployment.md) | Azure production deployment |
| 11 | [docs/ops/11-tls-termination-guide.md](docs/ops/11-tls-termination-guide.md) | TLS termination guide |
| 12 | [docs/ops/12-server-hardening-guide.md](docs/ops/12-server-hardening-guide.md) | Server hardening |
| 13 | [docs/ops/13-observability-guide.md](docs/ops/13-observability-guide.md) | Comprehensive observability guide |
| 14 | [docs/ops/14-sentry-configuration-guide.md](docs/ops/14-sentry-configuration-guide.md) | Sentry configuration |
| 16 | [docs/ops/16-backup-drill-guide.md](docs/ops/16-backup-drill-guide.md) | Backup drill guide (detailed) |
| 17 | [docs/ops/17-performance-optimization-guide.md](docs/ops/17-performance-optimization-guide.md) | Performance optimization |
| 18 | [docs/ops/18-compliance-guide.md](docs/ops/18-compliance-guide.md) | Compliance guide |
| 19 | [docs/ops/19-uat-procedures-guide.md](docs/ops/19-uat-procedures-guide.md) | UAT procedures |
| 20 | [docs/ops/20-sla-slo-baselines.md](docs/ops/20-sla-slo-baselines.md) | SLA/SLO baselines (detailed) |
| 23 | [docs/ops/23-environment-security-guide.md](docs/ops/23-environment-security-guide.md) | Environment security |
| 24 | [docs/ops/24-secrets-management-guide.md](docs/ops/24-secrets-management-guide.md) | Secrets management (main guide) |
| 25 | [docs/ops/25-azure-key-vault-integration.md](docs/ops/25-azure-key-vault-integration.md) | Azure Key Vault integration |
| 26 | [docs/ops/26-smtp-provider-selection.md](docs/ops/26-smtp-provider-selection.md) | SMTP provider selection |
| 27 | [docs/ops/27-azure-deployment-guide-extended.md](docs/ops/27-azure-deployment-guide-extended.md) | Extended Azure deployment |
| 28 | [docs/ops/28-logging-guide.md](docs/ops/28-logging-guide.md) | Logging guide |

> **Note**: #15, #21, #22 were removed during consolidation (duplicates/merged into other docs)

---

### 4. Legal & Compliance (docs/legal/)

| File | Description |
|------|-------------|
| [docs/legal/privacy-policy-template.md](docs/legal/privacy-policy-template.md) | Privacy policy template |
| [docs/legal/terms-of-service-template.md](docs/legal/terms-of-service-template.md) | Terms of service template |
| [docs/legal/data-retention-and-deletion-policy.md](docs/legal/data-retention-and-deletion-policy.md) | Data retention policy |

---

### 5. QA Templates (docs/templates/)

| File | Description |
|------|-------------|
| [docs/templates/uat-scenario-template.md](docs/templates/uat-scenario-template.md) | UAT scenario template |
| [docs/templates/bug-bash-report-template.md](docs/templates/bug-bash-report-template.md) | Bug bash report template |

---

## Recommended Reading Order

### For Developers (New to Project)

1. Start with: [docs/tech/18-Complete-Project-Summary.md](docs/tech/18-Complete-Project-Summary.md)
2. Then: [docs/tech/04-Complete-Build-And-Run-Guide.md](docs/tech/04-Complete-Build-And-Run-Guide.md)
3. Then: [docs/tech/02-Complete-Architecture-Decisions.md](docs/tech/02-Complete-Architecture-Decisions.md)
4. Then: [docs/tech/09-Complete-Modules-Detailed.md](docs/tech/09-Complete-Modules-Detailed.md)
5. Reference: [docs/tech/10-Complete-API-Routes-Reference.md](docs/tech/10-Complete-API-Routes-Reference.md)

### For Operations Team

1. Start with: [docs/ops/01-production-runbook.md](docs/ops/01-production-runbook.md)
2. Then: [docs/ops/13-observability-guide.md](docs/ops/13-observability-guide.md)
3. Then: [docs/ops/24-secrets-management-guide.md](docs/ops/24-secrets-management-guide.md)
4. Then: [docs/tech/13-Complete-Docker-Configuration.md](docs/tech/13-Complete-Docker-Configuration.md)

---

## Project Overview

The LMS Backend is a production-oriented Learning Management System built with FastAPI. Key features include:

- **Authentication**: JWT-based auth with role-based access control
- **Course Management**: Create and publish courses with lessons
- **Enrollments**: Track student progress
- **Quizzes**: Automated assessments with multiple question types
- **Certificates**: Auto-generated PDF certificates
- **Analytics**: Dashboards for students, instructors, admins
- **Background Tasks**: Celery for async processing

---

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Docker Development

```bash
docker compose up --build
```

### Production

```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Full Reference**: [09-full-api-reference.md](09-full-api-reference.md)

---

## Support

For questions or contributions:
1. Review relevant documentation in this folder
2. Check API docs at /docs when running locally
3. Examine test files in tests/ for patterns
4. Review module code in app/modules/

---

*Last Updated: 2026*
