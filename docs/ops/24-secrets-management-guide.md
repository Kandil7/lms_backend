# Secrets Management Guide

This document outlines the secrets management strategy for the LMS backend in production environments.

## 1. Overview

The LMS backend uses a layered approach to secrets management:

- **Primary**: HashiCorp Vault (recommended for production)
- **Fallback**: Environment variables (for development/staging)
- **Optional**: Azure Key Vault, GCP Secret Manager

The system automatically loads sensitive values from the configured secrets source during application startup.

## 2. Supported Secret Sources

### 2.1 HashiCorp Vault (Production Recommended)

**Configuration:**
- Set environment variables:
  - `VAULT_ADDR`: Vault server URL (e.g., `https://vault.example.com:8200`)
  - `VAULT_TOKEN`: Authentication token
  - `VAULT_NAMESPACE`: Optional namespace

**Vault Path Structure:**
```text
secret/data/lms/
|- SECRET_KEY
|- DATABASE_PASSWORD
|- SMTP_PASSWORD
|- SENTRY_DSN
|- AZURE_STORAGE_ACCOUNT_NAME
|- AZURE_STORAGE_ACCOUNT_KEY
`- ...
```

### 2.2 Environment Variables (Development/Staging)

**Environment Variables:**
- `SECRET_KEY`: Application secret key
- `DATABASE_PASSWORD`: Database password
- `SMTP_PASSWORD`: SMTP password
- `SENTRY_DSN`: Sentry DSN
- `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_ACCOUNT_KEY`: Azure Blob credentials

### 2.3 Azure Key Vault (Production on Azure)

**Configuration:**
- Set `AZURE_KEYVAULT_URL` (example: `https://your-vault-name.vault.azure.net/`).
- Ensure app identity/user has secret read permissions (RBAC role like `Key Vault Secrets Officer` for setup and a read role for runtime identity).

**Secret naming format used by application:**
- Prefix: `lms-`
- Key mapping: lowercase + replace `_` with `-`
- Example:
  - App key: `AZURE_STORAGE_CONNECTION_STRING`
  - Key Vault secret name: `lms-azure-storage-connection-string`

**Recommended Azure storage secrets in Key Vault:**
- `lms-azure-storage-connection-string`
- `lms-azure-storage-account-name`
- `lms-azure-storage-account-key`
- `lms-azure-storage-account-url`
- `lms-azure-storage-container-name`
- `lms-azure-storage-container-url`

## 3. Secret Loading Priority

The application follows this priority order:
1. Vault (if initialized successfully)
2. Environment variables with `SECRET_` prefix (e.g., `SECRET_SECRET_KEY`)
3. Direct environment variables (legacy compatibility)
4. Default values from configuration

## 4. Production Deployment Steps

### 4.1 Vault Setup
1. Create Vault policy for LMS application
2. Configure KV v2 secrets engine at `secret/data/lms`
3. Store secrets in Vault
4. Create AppRole or Token authentication

### 4.2 Application Configuration
1. Set `VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_NAMESPACE` in production environment
2. Ensure `ENVIRONMENT=production` is set
3. Verify secrets are loaded correctly in logs

### 4.3 Verification
Run the following command to verify secrets loading:
```bash
docker-compose -f docker-compose.prod.yml up --build
```

Check logs for:
- "Secrets manager initialized with source: vault"
- "SECRET_KEY loaded from secrets manager"

## 5. Security Best Practices

- Rotate secrets every 90 days
- Use short-lived tokens for Vault authentication
- Enable Vault audit logging
- Restrict Vault access to production infrastructure only
- Never commit secrets to version control

## 6. Troubleshooting

### Common Issues:
- **Vault connection failed**: Check network connectivity and authentication
- **Secret not found**: Verify path and key names in Vault
- **Fallback to environment variables**: Ensure production secrets are properly configured

### Debugging:
Set `LOG_LEVEL=DEBUG` to see detailed secrets loading information.
