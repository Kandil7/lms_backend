# Azure VM Deployment Script for LMS Backend (PowerShell)

param(
    [Parameter(Mandatory=$true)]
    [string]$AzureVMHost,
    
    [Parameter(Mandatory=$true)]
    [string]$AzureVMUser,
    
    [Parameter(Mandatory=$true)]
    [string]$ProdDatabaseUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$SecretKey,
    
    [Parameter(Mandatory=$true)]
    [string]$AppDomain,
    
    [Parameter(Mandatory=$true)]
    [string]$LetsEncryptEmail
)

Write-Host "Starting LMS backend deployment to Azure VM..."

# Validate required parameters
$requiredParams = @("AzureVMHost", "AzureVMUser", "ProdDatabaseUrl", "SecretKey", "AppDomain", "LetsEncryptEmail")
foreach ($param in $requiredParams) {
    if ([string]::IsNullOrEmpty((Get-Variable $param -ValueOnly))) {
        Write-Error "Required parameter '$param' not provided"
        exit 1
    }
}

try {
    # Create deployment directory on VM
    Write-Host "Creating deployment directory..."
    Invoke-Command -ComputerName $AzureVMHost -Credential (Get-Credential) -ScriptBlock {
        mkdir -p ~/lms-deployment
    }

    # Copy current codebase to VM using SCP (requires OpenSSH)
    Write-Host "Copying codebase to VM..."
    $tempZip = "$env:TEMP\lms-backend.zip"
    Compress-Archive -Path .\* -DestinationPath $tempZip -Force
    
    # Use scp to copy (requires OpenSSH installed on Windows)
    $scpCommand = "scp -o StrictHostKeyChecking=no `"$tempZip`" $AzureVMUser@$AzureVMHost:~/lms-deployment/"
    Invoke-Expression $scpCommand
    
    Remove-Item $tempZip

    # Extract and prepare on VM
    Write-Host "Extracting and preparing on VM..."
    $deployScript = @"
cd ~/lms-deployment
unzip lms-backend.zip
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
PROD_DATABASE_URL=$ProdDatabaseUrl

# Security
SECRET_KEY=$SecretKey
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
APP_DOMAIN=$AppDomain
LETSENCRYPT_EMAIL=$LetsEncryptEmail

# CORS / Hosts
CORS_ORIGINS=https://$AppDomain
TRUSTED_HOSTS=$AppDomain

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
    echo "Access API at: https://$AppDomain/api/v1/ready"
else
    echo "❌ Deployment failed - API not responding"
    exit 1
fi
"@

    Invoke-Command -ComputerName $AzureVMHost -Credential (Get-Credential) -ScriptBlock {
        param($script)
        $script | Out-File -FilePath ~/deploy.sh -Encoding UTF8
        chmod +x ~/deploy.sh
        bash ~/deploy.sh
    } -ArgumentList $deployScript

    Write-Host "Deployment completed successfully!"
}
catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
}