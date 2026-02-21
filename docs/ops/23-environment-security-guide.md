# Environment Security Guide

This document outlines secure environment configuration practices for the LMS backend in production environments.

## 1. Overview

Environment files contain sensitive configuration that must be handled securely. The current `.env.*.example` files contain hardcoded secrets that pose significant security risks if used in production.

## 2. Current Security Issues

### 2.1 Critical Vulnerabilities
- **Hardcoded database passwords**: `change-strong-db-password` in `.env.staging.example` and `.env.production.example`
- **Hardcoded secret keys**: `replace-with-a-strong-random-secret-at-least-32-chars` in staging example
- **Missing secret rotation procedures**: No automated secret rotation
- **Insecure default values**: Weak defaults that could be accidentally deployed

### 2.2 Risk Assessment
| Issue | Severity | Impact | Likelihood |
|-------|----------|--------|------------|
| Hardcoded DB passwords | Critical | Full database compromise | High (if env files committed) |
| Weak secret key defaults | Critical | Authentication bypass | Medium (if defaults not changed) |
| Missing secret rotation | High | Long-term credential exposure | High |

## 3. Secure Environment Configuration Strategy

### 3.1 Environment File Management
#### Production Environment Files
- **Never commit** `.env.production` or `.env.staging` to version control
- Use `.gitignore` to exclude all `.env.*` files except examples
- Store production environment files in secure location (Vault, encrypted storage)

#### Example Files Best Practices
- **Remove hardcoded secrets** from example files
- Use placeholder format that clearly indicates required values
- Add security warnings and instructions

### 3.2 Recommended Example File Format
```env
# .env.production.example
# SECURITY WARNING: This is an EXAMPLE file only. DO NOT use these values in production.
# Replace ALL placeholder values before deployment.

# Application
PROJECT_NAME=LMS Backend
ENVIRONMENT=production
DEBUG=false
ENABLE_API_DOCS=false
STRICT_ROUTER_IMPORTS=true
METRICS_ENABLED=true

# Database - REPLACE WITH SECURE VALUES
POSTGRES_USER=lms
POSTGRES_PASSWORD=<REDACTED>  # Must be strong password (16+ chars)
POSTGRES_DB=lms
DATABASE_URL=postgresql+psycopg2://lms:<REDACTED>@db:5432/lms

# Security - REPLACE WITH SECURE VALUES
SECRET_KEY=<REDACTED>  # Must be 32+ random characters
ALGORITHM=HS256

# Secrets Management - Configure Vault integration
VAULT_ADDR=https://vault.example.com:8200
VAULT_TOKEN=<REDACTED>  # Short-lived token or AppRole credentials
VAULT_NAMESPACE=prod

# Sensitive credentials - Load from secrets manager
SENTRY_DSN=<REDACTED>
SMTP_HOST=<REDACTED>
SMTP_USERNAME=<REDACTED>
SMTP_PASSWORD=<REDACTED>
AWS_ACCESS_KEY_ID=<REDACTED>
AWS_SECRET_ACCESS_KEY=<REDACTED>

# Instructions:
# 1. Create production environment file: cp .env.production.example .env.production
# 2. Replace all <REDACTED> values with secure credentials
# 3. Store .env.production in secure location (NOT in git)
# 4. Use secrets manager for production deployments
```

## 4. Implementation Steps

### 4.1 Immediate Actions
1. **Update example files** to remove hardcoded secrets
2. **Add security warnings** to all example files
3. **Update .gitignore** to ensure no env files are committed
4. **Create secure environment template** for production deployment

### 4.2 Environment File Validation Script
Create a validation script to check for security issues:

```bash
#!/bin/bash
# validate_env.sh
# Usage: ./validate_env.sh .env.production

FILE="$1"

if [ ! -f "$FILE" ]; then
    echo "Error: File $FILE not found"
    exit 1
fi

echo "Validating environment file: $FILE"

# Check for hardcoded secrets
if grep -q "change-strong-db-password" "$FILE"; then
    echo "❌ CRITICAL: Hardcoded database password detected"
    exit 1
fi

if grep -q "replace-with-a-strong-random-secret" "$FILE"; then
    echo "❌ CRITICAL: Hardcoded secret key detected"
    exit 1
fi

if grep -q "admin" "$FILE" && grep -q "password" "$FILE"; then
    echo "⚠️  Warning: Admin credentials pattern detected"
fi

echo "✅ Environment file validation passed"
```

### 4.3 CI/CD Integration
Add environment validation to CI/CD pipeline:
```yaml
# GitHub Actions example
- name: Validate environment files
  run: |
    ./scripts/validate_env.sh .env.staging
    ./scripts/validate_env.sh .env.production
  if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
```

## 5. Secret Management Integration

### 5.1 Environment Variable Priority
The application should follow this priority order:
1. **Vault secrets** (highest priority)
2. **Environment variables** (for development/staging)
3. **Default values** (lowest priority, only for development)

### 5.2 Production Deployment Process
1. **Generate secure secrets** using `openssl rand -hex 32`
2. **Store secrets in Vault** using appropriate policies
3. **Configure environment variables** for non-sensitive settings
4. **Deploy with secrets manager integration**
5. **Verify secret loading** during startup

## 6. Security Best Practices

### 6.1 Environment File Handling
- **Never commit** `.env.*` files to version control
- **Use encrypted storage** for production environment files
- **Rotate secrets** every 90 days
- **Audit access** to environment files
- **Monitor for accidental commits** (pre-commit hooks, CI checks)

### 6.2 Development vs Production
| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| Secret source | Environment variables | Environment variables + Vault | Vault only |
| Debug mode | true | false | false |
| API docs | enabled | disabled | disabled |
| Rate limiting | disabled | enabled | enabled |
| Logging level | DEBUG | INFO | INFO/WARNING |

## 7. Compliance Requirements

### 7.1 GDPR/CCPA
- Environment files containing PII must be encrypted at rest
- Access to environment files must be logged and audited
- Secret rotation must comply with data retention policies

### 7.2 SOC 2
- Environment file management must follow change control procedures
- Access to production environment files requires multi-factor authentication
- Regular security reviews of environment configuration

## 8. Templates and Tools

### 8.1 Secure Environment Template
```env
# .env.production.secure.template
# This template should be used to create production environment files
# Store this template in secure location, NOT in git

# Application configuration
PROJECT_NAME=LMS Backend
ENVIRONMENT=production
DEBUG=false
ENABLE_API_DOCS=false
STRICT_ROUTER_IMPORTS=true

# Database configuration - MUST BE SECURE
POSTGRES_USER=lms
POSTGRES_PASSWORD=${SECRET_POSTGRES_PASSWORD}
POSTGRES_DB=lms
DATABASE_URL=postgresql+psycopg2://lms:${SECRET_POSTGRES_PASSWORD}@db:5432/lms

# Security configuration - MUST BE SECURE
SECRET_KEY=${SECRET_APPLICATION_KEY}
ALGORITHM=HS256

# Secrets management configuration
VAULT_ADDR=${SECRET_VAULT_ADDR}
VAULT_TOKEN=${SECRET_VAULT_TOKEN}
VAULT_NAMESPACE=prod

# Other sensitive configurations
SENTRY_DSN=${SECRET_SENTRY_DSN}
SMTP_HOST=${SECRET_SMTP_HOST}
SMTP_USERNAME=${SECRET_SMTP_USERNAME}
SMTP_PASSWORD=${SECRET_SMTP_PASSWORD}

# Instructions:
# 1. Create .env.production from this template
# 2. Replace ${SECRET_*} placeholders with actual secrets
# 3. Store .env.production in secure location
# 4. Use secrets manager for automated deployments
```

## 9. Verification and Sign-off

### 9.1 Pre-Production Checklist
- [ ] All example files updated to remove hardcoded secrets
- [ ] Environment validation script implemented
- [ ] CI/CD integration for environment validation
- [ ] Secure environment template created
- [ ] Team trained on secure environment management

### 9.2 Evidence Required
- Signed security review of environment configuration
- Environment validation script results
- Proof of secret rotation procedures
- Access control documentation for environment files

## 10. Next Steps

1. **Update all example files** to remove hardcoded secrets (this week)
2. **Implement environment validation script** (next 2 days)
3. **Integrate with CI/CD pipeline** (1 week)
4. **Train team on secure environment practices** (2 weeks)
5. **Complete final security review** (pre-launch)

This guide provides comprehensive security practices for environment configuration and ensures the LMS backend meets production security requirements.