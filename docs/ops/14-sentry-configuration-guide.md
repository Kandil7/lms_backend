# Sentry Configuration Guide

This document outlines the Sentry configuration strategy for the LMS backend in production environments.

## 1. Overview

Sentry is configured for both API and Celery worker monitoring with:
- **API Integration**: FastAPI/Starlette integration for web requests
- **Celery Integration**: Celery integration for background tasks
- **Environment-based routing**: Different environments (development, staging, production) use separate projects

## 2. Configuration Parameters

### 2.1 Required Environment Variables
- `SENTRY_DSN`: Sentry Data Source Name (required for production)
- `SENTRY_ENVIRONMENT`: Environment name (defaults to `ENVIRONMENT` value)
- `SENTRY_RELEASE`: Release version (defaults to `VERSION`)
- `SENTRY_TRACES_SAMPLE_RATE`: Tracing sampling rate (0.0-1.0)
- `SENTRY_PROFILES_SAMPLE_RATE`: Profiling sampling rate (0.0-1.0)
- `SENTRY_SEND_PII`: Whether to send personally identifiable information
- `SENTRY_ENABLE_FOR_CELERY`: Whether to enable Sentry for Celery workers

### 2.2 Secret Management Integration
In production, Sentry DSN is loaded from secrets manager:
- Vault path: `secret/data/lms/SENTRY_DSN`
- Environment variable fallback: `SENTRY_DSN`
- Default: None (required for production)

## 3. Production Configuration

### 3.1 Recommended Settings for Production
```env
SENTRY_DSN=https://your-dsn@sentry.io/123456
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=1.0.0
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.0
SENTRY_SEND_PII=false
SENTRY_ENABLE_FOR_CELERY=true
```

### 3.2 Environment-Specific Configuration
- **Development**: `SENTRY_DSN` can be empty or use development project
- **Staging**: Use staging Sentry project with `SENTRY_ENVIRONMENT=staging`
- **Production**: Must have valid `SENTRY_DSN` and proper environment settings

## 4. Verification Steps

### 4.1 Test Initialization
```bash
# Test API Sentry initialization
docker-compose -f docker-compose.prod.yml run --rm api python -c "from app.core.observability import init_sentry_for_api; init_sentry_for_api()"

# Test Celery Sentry initialization  
docker-compose -f docker-compose.prod.yml run --rm celery-worker python -c "from app.core.observability import init_sentry_for_celery; init_sentry_for_celery()"
```

### 4.2 Manual Test Events
Create test files to verify Sentry is working:

**test_sentry.py:**
```python
import sentry_sdk
from sentry_sdk import capture_exception, capture_message

# Test error capture
try:
    1 / 0
except Exception as e:
    capture_exception(e)

# Test message capture
capture_message("Test message from LMS backend")

# Test transaction tracing
with sentry_sdk.start_transaction(op="test", name="test_transaction"):
    print("Testing transaction")
```

Run with:
```bash
python test_sentry.py
```

### 4.3 Verify in Sentry UI
- Check Issues tab for captured errors
- Check Performance tab for transactions
- Verify environment filtering works correctly
- Confirm release versions are properly tagged

## 5. Alerting Configuration

### 5.1 Sentry Alerts
Configure alerts in Sentry UI:
- **Critical**: Unhandled exceptions, 5xx errors > 5% rate
- **Warning**: High latency (> 2s), frequent rate limit violations
- **Info**: Deployment notifications, scheduled maintenance

### 5.2 Integration with Alertmanager
For unified alerting, configure:
- Webhook integration between Sentry and Alertmanager
- Duplicate suppression to avoid alert storms
- Escalation policies for critical issues

## 6. Security Best Practices

### 6.1 PII Handling
- Set `SENTRY_SEND_PII=false` in production
- Use data scrubbing rules in Sentry UI
- Mask sensitive fields (passwords, tokens, PII)
- Review Sentry data retention policies

### 6.2 Access Control
- Restrict Sentry project access to authorized personnel
- Use role-based access control in Sentry
- Enable SSO for team authentication
- Regularly review access logs

## 7. Troubleshooting

### Common Issues:
- **"Failed to initialize Sentry"**: Verify SENTRY_DSN is set and valid
- **No events appearing**: Check network connectivity to Sentry
- **High sampling rates causing performance issues**: Reduce `SENTRY_TRACES_SAMPLE_RATE`
- **PII leakage**: Enable data scrubbing and set `SENTRY_SEND_PII=false`

### Debugging Commands:
```bash
# Check Sentry SDK version
pip show sentry-sdk

# Test network connectivity
curl -I https://sentry.io

# Verify configuration
python -c "from app.core.config import get_settings; print(get_settings().SENTRY_DSN)"
```

## 8. Documentation Requirements

- Sentry project setup documentation
- Alert configuration and escalation procedures
- Incident response procedures for Sentry alerts
- Regular review of Sentry data and costs