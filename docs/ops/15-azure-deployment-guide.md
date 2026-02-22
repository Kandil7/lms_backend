# Azure Deployment Guide for LMS Backend

This comprehensive guide provides step-by-step instructions for deploying the LMS backend to Azure production environment.

## 1. Prerequisites

### 1.1 Azure Resources Required
- Azure VM (Ubuntu 22.04 LTS recommended)
- Azure Database for PostgreSQL Flexible Server
- Azure Key Vault (for production secrets)
- DNS domain name (for TLS/SSL)

### 1.2 Local Requirements
- Azure CLI installed and configured
- SSH key pair for VM access
- Docker and Docker Compose installed on local machine
- PowerShell or Bash shell

## 2. Step-by-Step Deployment

### 2.1 Create Azure Resources

#### 2.1.1 Azure VM
```bash
# Create resource group
az group create --name lms-rg --location eastus

# Create VM (Ubuntu 22.04)
az vm create \
  --resource-group lms-rg \
  --name lms-vm \
  --image Ubuntu2204 \
  --size Standard_D2s_v3 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard \
  --size Standard_D2s_v3

# Get VM public IP
az vm show -g lms-rg -n lms-vm --query publicIps -o tsv
```

#### 2.1.2 Azure PostgreSQL Flexible Server
```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group lms-rg \
  --name lms-postgres \
  --location eastus \
  --admin-user lmsadmin \
  --admin-password "StrongPassword123!" \
  --sku-name Standard_D2s_v3 \
  --tier GeneralPurpose \
  --version 16 \
  --high-availability ZoneRedundant \
  --storage-size 128

# Create database
az postgres flexible-server db create \
  --resource-group lms-rg \
  --server-name lms-postgres \
  --database-name lms

# Allow VM IP access
VM_IP=$(az vm show -g lms-rg -n lms-vm --query publicIps -o tsv)
az postgres flexible-server firewall-rule create \
  --resource-group lms-rg \
  --server-name lms-postgres \
  --rule-name allow-lms-vm \
  --start-ip-address $VM_IP \
  --end-ip-address $VM_IP
```

#### 2.1.3 Azure Key Vault (Optional but Recommended)
```bash
# Create Key Vault
az keyvault create \
  --name lms-keyvault \
  --resource-group lms-rg \
  --location eastus \
  --sku standard

# Create managed identity for VM
az vm identity assign \
  --resource-group lms-rg \
  --name lms-vm \
  --identity-type SystemAssigned

# Get VM principal ID
VM_PRINCIPAL_ID=$(az vm show -g lms-rg -n lms-vm --query identity.principalId -o tsv)

# Set Key Vault access policy
az keyvault set-access-policy \
  --name lms-keyvault \
  --object-id $VM_PRINCIPAL_ID \
  --secret-permissions get list
```

### 2.2 Configure DNS and TLS

#### 2.2.1 DNS Configuration
1. Create A record in your DNS provider:
   - Name: `api` (or your desired subdomain)
   - Value: VM public IP address
   - TTL: 300 seconds

#### 2.2.2 TLS Configuration with Caddy
The LMS backend uses Caddy for automatic TLS certificate management with Let's Encrypt.

**Required environment variables:**
- `APP_DOMAIN`: Your API domain (e.g., `api.yourdomain.com`)
- `LETSENCRYPT_EMAIL`: Email for certificate notifications

### 2.3 Deploy LMS Backend

#### 2.3.1 Using GitHub Actions (Recommended)
1. Set up GitHub Environment secrets:
   - `AZURE_VM_HOST`: VM public IP
   - `AZURE_VM_USER`: VM username (e.g., `azureuser`)
   - `AZURE_VM_SSH_KEY`: Private SSH key (base64 encoded)
   - `PROD_DATABASE_URL`: PostgreSQL connection string
   - `SECRET_KEY`: Strong 32+ character secret key
   - `APP_DOMAIN`: Your API domain
   - `LETSENCRYPT_EMAIL`: Email for Let's Encrypt
   - `FRONTEND_BASE_URL`: Frontend URL
   - `CORS_ORIGINS`: Frontend origins
   - `TRUSTED_HOSTS`: Trusted hosts
   - `SMTP_*`: SMTP configuration
   - `SENTRY_DSN`: Sentry DSN (optional)

2. Push to `main` branch to trigger deployment

#### 2.3.2 Manual Deployment
1. **Prepare local environment:**
   ```bash
   # Set required environment variables
   export AZURE_VM_HOST="your-vm-ip"
   export AZURE_VM_USER="azureuser"
   export PROD_DATABASE_URL="postgresql+psycopg2://lmsadmin:password@lms-postgres.postgres.database.azure.com:5432/lms?sslmode=require"
   export SECRET_KEY="your-strong-32-character-secret-key"
   export APP_DOMAIN="api.yourdomain.com"
   export LETSENCRYPT_EMAIL="ops@yourdomain.com"
   ```

2. **Run deployment script:**
   ```bash
   # For Linux/macOS
   bash scripts/deploy_azure_vm.sh

   # For Windows (PowerShell)
   .\scripts\deploy_azure_vm.ps1 -AzureVMHost $env:AZURE_VM_HOST -AzureVMUser $env:AZURE_VM_USER -ProdDatabaseUrl $env:PROD_DATABASE_URL -SecretKey $env:SECRET_KEY -AppDomain $env:APP_DOMAIN -LetsEncryptEmail $env:LETSENCRYPT_EMAIL
   ```

### 2.4 Post-Deployment Verification

#### 2.4.1 Service Health Check
```bash
# Check if services are running
ssh azureuser@your-vm-ip "docker ps -a"

# Verify API is accessible
curl -f https://api.yourdomain.com/api/v1/ready

# Check logs
ssh azureuser@your-vm-ip "docker logs lms-backend-api-1"
```

#### 2.4.2 Security Verification
- Verify TLS certificate: `openssl s_client -connect api.yourdomain.com:443`
- Check security headers: `curl -I https://api.yourdomain.com`
- Verify Azure Key Vault integration (if used): Check application logs

## 3. Production Configuration

### 3.1 Environment Variables Reference
| Variable | Description | Required |
|----------|-------------|----------|
| `ENVIRONMENT` | Set to `production` | ✅ |
| `DEBUG` | Set to `false` | ✅ |
| `PROD_DATABASE_URL` | PostgreSQL connection string | ✅ |
| `SECRET_KEY` | JWT secret key (32+ chars) | ✅ |
| `APP_DOMAIN` | API domain name | ✅ |
| `LETSENCRYPT_EMAIL` | Let's Encrypt email | ✅ |
| `FRONTEND_BASE_URL` | Frontend URL | ✅ |
| `CORS_ORIGINS` | Frontend origins | ✅ |
| `TRUSTED_HOSTS` | Trusted hosts | ✅ |
| `SMTP_*` | SMTP configuration | ✅ for email features |
| `SENTRY_DSN` | Sentry error tracking | ❌ optional |

### 3.2 Azure-Specific Optimizations
- **VM Size**: Start with Standard_D2s_v3, scale as needed
- **PostgreSQL**: Use Flexible Server with Zone Redundancy for HA
- **Backup**: Enable automated backups in PostgreSQL
- **Monitoring**: Enable Azure Monitor for VM and PostgreSQL

## 4. Troubleshooting

### 4.1 Common Issues
- **Caddy TLS failure**: Verify DNS A record points to correct IP
- **Database connection refused**: Verify PostgreSQL firewall rules
- **Docker build failures**: Check Docker daemon status on VM
- **API 502 errors**: Verify Caddy is proxying to correct port

### 4.2 Diagnostic Commands
```bash
# Check Caddy logs
ssh azureuser@vm-ip "docker logs lms-backend-caddy-1"

# Check API logs
ssh azureuser@vm-ip "docker logs lms-backend-api-1"

# Test database connectivity
ssh azureuser@vm-ip "PGPASSWORD='password' psql -h lms-postgres.postgres.database.azure.com -U lmsadmin -d lms -c 'SELECT 1'"

# Check network connectivity
ssh azureuser@vm-ip "curl -v http://localhost:8000/api/v1/ready"
```

## 5. Scaling and High Availability

### 5.1 Horizontal Scaling
- Add more API instances behind load balancer
- Scale Celery workers based on queue depth
- Use Redis cluster for distributed caching

### 5.2 Disaster Recovery
- Regular database backups (enabled by default in PostgreSQL Flexible Server)
- VM image snapshots
- Multi-region deployment for critical systems

## Appendix A: Sample Production .env File

```env
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false
ENABLE_API_DOCS=false
STRICT_ROUTER_IMPORTS=true
METRICS_ENABLED=true
API_RESPONSE_ENVELOPE_ENABLED=true
API_RESPONSE_SUCCESS_MESSAGE=Success

# Database
PROD_DATABASE_URL=postgresql+psycopg2://lmsadmin:StrongPassword123!@lms-postgres.postgres.database.azure.com:5432/lms?sslmode=require

# Security
SECRET_KEY=your-strong-32-character-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES=1440
REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN=true
MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES=10
MFA_LOGIN_CODE_EXPIRE_MINUTES=10
MFA_LOGIN_CODE_LENGTH=6
ACCESS_TOKEN_BLACKLIST_ENABLED=true
ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED=true

# Domain / TLS
APP_DOMAIN=api.yourdomain.com
LETSENCRYPT_EMAIL=ops@yourdomain.com

# CORS / Hosts
CORS_ORIGINS=https://app.yourdomain.com
TRUSTED_HOSTS=api.yourdomain.com

# Redis / Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
TASKS_FORCE_INLINE=false
RATE_LIMIT_USE_REDIS=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_REDIS_PREFIX=ratelimit

# File Uploads
UPLOAD_DIR=uploads
CERTIFICATES_DIR=certificates
MAX_UPLOAD_MB=100
ALLOWED_UPLOAD_EXTENSIONS=mp4,avi,mov,pdf,doc,docx,jpg,jpeg,png
FILE_STORAGE_PROVIDER=local
FILE_DOWNLOAD_URL_EXPIRE_SECONDS=900
```

**Note**: Replace placeholder values with your actual configuration.