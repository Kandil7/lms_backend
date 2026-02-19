# Security Sign-off and Hardening

## 1. Security Sign-off Gate
- `security.yml` must be green on release commit:
  - dependency scan (`pip-audit`)
  - static scan (`bandit`)
  - secret scan (`gitleaks`)
- No unresolved high/critical findings.

## 2. Secrets Management Requirements
- Do not store production secrets in `.env` files in git.
- Use one of:
  - HashiCorp Vault
  - AWS Secrets Manager
  - GCP Secret Manager
- Minimum managed secrets:
  - `SECRET_KEY`
  - database password
  - SMTP credentials
  - `SENTRY_DSN`
  - S3 credentials (if used)

## 3. Secret Rotation Policy
- Rotation interval:
  - app secrets: every 90 days
  - DB/SMTP credentials: every 90 days
  - emergency rotation: immediate after incident
- Verify rollout in staging before production.

## 4. Server Hardening Baseline
- OS patching enabled and reviewed weekly.
- Firewall allows only required ports (`80/443` and explicit admin channels).
- SSH hardening:
  - key-based login only
  - disable root login
  - fail2ban enabled
- Run containers/services with least privilege.
- TLS termination with modern ciphers and HSTS.
- Log retention and centralization enabled.

## 5. Release Security Checklist
- [ ] `security.yml` green
- [ ] no hardcoded secrets in diff
- [ ] all production secrets fetched from secret manager
- [ ] docs/openapi disabled in production
- [ ] rate limiting enabled with Redis backend
- [ ] hardening baseline verified

