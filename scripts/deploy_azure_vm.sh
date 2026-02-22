#!/bin/bash
# Azure VM Deployment Script for LMS Backend

set -e

echo "Starting LMS backend deployment to Azure VM..."

# Validate required environment variables
required_vars=("AZURE_VM_HOST" "AZURE_VM_USER" "PROD_DATABASE_URL" "SECRET_KEY" "APP_DOMAIN" "LETSENCRYPT_EMAIL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var not set"
        exit 1
    fi
done

# Create deployment directory on VM
echo "Creating deployment directory..."
ssh "$AZURE_VM_USER@$AZURE_VM_HOST" "mkdir -p ~/lms-deployment"

# Copy current codebase to VM
echo "Copying codebase to VM..."
tar -czf lms-backend.tar.gz --exclude='node_modules' --exclude='.git' --exclude='__pycache__' .
scp lms-backend.tar.gz "$AZURE_VM_USER@$AZURE_VM_HOST":~/lms-deployment/
rm lms-backend.tar.gz

# Extract and prepare on VM
echo "Extracting and preparing on VM..."
ssh "$AZURE_VM_USER@$AZURE_VM_HOST" << EOF
cd ~/lms-deployment
tar -xzf lms-backend.tar.gz
cd lms-backend

# Create production environment file
cat > .env << EOL
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false
ENABLE_API_DOCS=false
STRICT_ROUTER_IMPORTS=true
METRICS_ENABLED=true
API_RESPONSE_ENVELOPE_ENABLED=true
API_RESPONSE_SUCCESS_MESSAGE=Success

# Database
PROD_DATABASE_URL=${PROD_DATABASE_URL}

# Security
SECRET_KEY=${SECRET_KEY}
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
APP_DOMAIN=${APP_DOMAIN}
LETSENCRYPT_EMAIL=${LETSENCRYPT_EMAIL}

# CORS / Hosts
CORS_ORIGINS=https://${APP_DOMAIN}
TRUSTED_HOSTS=${APP_DOMAIN}

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

# Optional Azure Blob Storage (if needed)
# AZURE_STORAGE_CONNECTION_STRING=
# AZURE_STORAGE_ACCOUNT_NAME=
# AZURE_STORAGE_ACCOUNT_KEY=
EOL

# Install dependencies
pip install -r requirements.txt

# Build Docker images
docker compose -f docker-compose.prod.yml build

# Start services
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Verify deployment
if curl -sf http://localhost:8000/api/v1/ready; then
    echo "✅ LMS backend deployed successfully!"
    echo "Access API at: https://${APP_DOMAIN}/api/v1/ready"
else
    echo "❌ Deployment failed - API not responding"
    exit 1
fi
EOF

echo "Deployment completed successfully!"