# Azure Key Vault Integration Guide

This document provides detailed instructions for integrating Azure Key Vault with the LMS backend for secure secret management in production environments.

## 1. Prerequisites

### Azure Resources Required
- Azure Key Vault instance
- Azure Managed Identity (for App Service/VM authentication) OR
- Service Principal with appropriate permissions

### Required Permissions
The identity used to access Key Vault must have:
- `get` permission on secrets
- `list` permission on secrets

## 2. Azure Key Vault Setup

### 2.1 Create Azure Key Vault
```bash
az keyvault create \
  --name <your-keyvault-name> \
  --resource-group <your-resource-group> \
  --location <your-location> \
  --sku standard
```

### 2.2 Configure Access Policies
For Managed Identity (recommended for Azure App Services):
```bash
# Get the managed identity principal ID
az webapp identity show --name <app-name> --resource-group <resource-group> --query principalId -o tsv

# Set access policy for the managed identity
az keyvault set-access-policy \
  --name <your-keyvault-name> \
  --object-id <managed-identity-principal-id> \
  --secret-permissions get list
```

For Service Principal:
```bash
az keyvault set-access-policy \
  --name <your-keyvault-name> \
  --spn <service-principal-client-id> \
  --secret-permissions get list
```

## 3. Secret Naming Convention

Azure Key Vault uses a specific naming convention for secrets:

| Configuration Variable | Azure Key Vault Secret Name |
|------------------------|----------------------------|
| SECRET_KEY | lms-secret-key |
| DATABASE_PASSWORD | lms-database-password |
| SMTP_PASSWORD | lms-smtp-password |
| SENTRY_DSN | lms-sentry-dsn |
| AZURE_STORAGE_CONNECTION_STRING | lms-azure-storage-connection-string |
| AZURE_STORAGE_ACCOUNT_NAME | lms-azure-storage-account-name |
| AZURE_STORAGE_ACCOUNT_KEY | lms-azure-storage-account-key |

**Note**: All secret names are prefixed with `lms-` and use lowercase with hyphens.

## 4. Environment Variables for Production

Add these environment variables to your production deployment:

### For Managed Identity Authentication (Recommended)
```env
# Azure Key Vault endpoint
AZURE_KEYVAULT_URL=https://<your-keyvault-name>.vault.azure.net
AZURE_KEYVAULT_ENDPOINT=https://<your-keyvault-name>.vault.azure.net

# Optional: If using Managed Identity with specific client ID
AZURE_CLIENT_ID=<managed-identity-client-id>
```

### For Service Principal Authentication
```env
# Azure Key Vault endpoint
AZURE_KEYVAULT_URL=https://<your-keyvault-name>.vault.azure.net

# Service Principal credentials
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<service-principal-client-id>
AZURE_CLIENT_SECRET=<service-principal-client-secret>
```

## 5. Deployment Configuration

### Docker Compose (Production)
In your `docker-compose.prod.yml`, add the Azure Key Vault environment variables:

```yaml
services:
  api:
    environment:
      - AZURE_KEYVAULT_URL=https://your-keyvault.vault.azure.net
      # For Managed Identity (Azure App Service/VM)
      - AZURE_CLIENT_ID=${AZURE_CLIENT_ID:-}
      # For Service Principal (if not using Managed Identity)
      - AZURE_TENANT_ID=${AZURE_TENANT_ID:-}
      - AZURE_CLIENT_ID=${AZURE_CLIENT_ID:-}
      - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET:-}
```

### Kubernetes Deployment
```yaml
env:
  - name: AZURE_KEYVAULT_URL
    value: "https://your-keyvault.vault.azure.net"
  - name: AZURE_CLIENT_ID
    valueFrom:
      secretKeyRef:
        name: azure-credentials
        key: client-id
```

## 6. Secret Management Workflow

### 6.1 Creating Secrets in Azure Key Vault
```bash
# Create secret for SECRET_KEY
az keyvault secret set \
  --vault-name <your-keyvault-name> \
  --name lms-secret-key \
  --value "your-strong-32-character-secret-key"

# Create secret for database password
az keyvault secret set \
  --vault-name <your-keyvault-name> \
  --name lms-database-password \
  --value "your-database-password"

# Create secret for SMTP password
az keyvault secret set \
  --vault-name <your-keyvault-name> \
  --name lms-smtp-password \
  --value "your-smtp-password"

# Create secret for Sentry DSN
az keyvault secret set \
  --vault-name <your-keyvault-name> \
  --name lms-sentry-dsn \
  --value "your-sentry-dsn"
```

### 6.2 Rotating Secrets
When rotating secrets, follow this process:
1. Create new secret with new value
2. Update application configuration to use new secret (if needed)
3. Wait for application restart/reload
4. Delete old secret after verification

## 7. Verification Steps

### 7.1 Test Azure Key Vault Connection
Run this test script to verify connectivity:
```python
from app.core.secrets import initialize_secrets_manager, get_secret

# Initialize with Azure Key Vault
success = initialize_secrets_manager("azure_key_vault")
print(f"Azure Key Vault initialization: {success}")

# Test secret retrieval
secret_key = get_secret("SECRET_KEY")
print(f"SECRET_KEY retrieved: {'Yes' if secret_key else 'No'}")

# Test database password
db_password = get_secret("DATABASE_PASSWORD")
print(f"DATABASE_PASSWORD retrieved: {'Yes' if db_password else 'No'}")
```

### 7.2 Application Startup Verification
Check application logs for these messages:
- `Secrets manager initialized with source: azure_key_vault`
- `Azure Key Vault authenticated via: Managed Identity`
- `Secret KEY retrieved successfully`

## 8. Fallback Mechanisms

The system includes robust fallback mechanisms:
1. **Primary**: Azure Key Vault
2. **Secondary**: HashiCorp Vault
3. **Tertiary**: Environment variables

If Azure Key Vault fails, the system will automatically fall back to the next available source.

## 9. Security Best Practices

- Never store secrets in source control
- Use Azure Key Vault's built-in audit logging
- Enable soft delete and purge protection for Key Vault
- Rotate secrets regularly (every 90 days recommended)
- Use separate Key Vaults for different environments (dev, staging, prod)

## 10. Troubleshooting

### Common Issues
- **Authentication failed**: Verify Managed Identity is assigned and has proper permissions
- **Secret not found**: Check secret naming convention (`lms-` prefix)
- **Network connectivity**: Ensure VNet integration or private endpoints are configured

### Debugging Steps
1. Check application logs for detailed error messages
2. Verify Azure Key Vault access policies
3. Test connectivity using Azure CLI
4. Validate secret names and values

## Appendix A: Sample .env.production.example with Azure Key Vault

```env
# Application
PROJECT_NAME=LMS Backend
ENVIRONMENT=production
DEBUG=false
ENABLE_API_DOCS=false
STRICT_ROUTER_IMPORTS=true
METRICS_ENABLED=true

# Azure Key Vault Configuration (Required for production)
AZURE_KEYVAULT_URL=https://your-lms-keyvault.vault.azure.net
# For Managed Identity (Azure App Service/VM)
# AZURE_CLIENT_ID=your-managed-identity-client-id

# Database (values will be overridden by Azure Key Vault)
POSTGRES_USER=lmsadmin
POSTGRES_PASSWORD=change-strong-local-db-password
DATABASE_URL=postgresql+psycopg2://lmsadmin:change-strong-azure-db-password@your-server.postgres.database.azure.com:5432/lms?sslmode=require

# Security (values will be overridden by Azure Key Vault)
SECRET_KEY=replace-with-a-strong-random-secret-at-least-32-chars
SMTP_PASSWORD=re_xxxxxxxxxxxxxxxxxxxxx
SENTRY_DSN=

# Domain / TLS
APP_DOMAIN=api.example.com
LETSENCRYPT_EMAIL=ops@example.com
```

**Note**: The actual secret values should be stored in Azure Key Vault, not in the .env file.