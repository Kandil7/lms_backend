# Azure VM Demo Deployment Script for LMS Backend (PowerShell)

param(
    [Parameter(Mandatory = $true)]
    [string]$AzureVMHost,

    [Parameter(Mandatory = $true)]
    [string]$AzureVMUser,

    [Parameter(Mandatory = $true)]
    [string]$AppDomain,

    [Parameter(Mandatory = $true)]
    [string]$LetsEncryptEmail,

    [Parameter(Mandatory = $true)]
    [string]$SecretKey,

    [string]$AppDir = "/opt/lms_backend_demo",
    [string]$SshPrivateKeyPath = "$HOME/.ssh/id_rsa",
    [int]$SshPort = 22,

    [string]$FrontendBaseUrl = "",
    [string]$CorsOrigins = "",
    [string]$TrustedHosts = "",
    [string]$PostgresUser = "lms_demo",
    [string]$PostgresPassword = "lms_demo",
    [string]$PostgresDb = "lms_demo",
    [string]$DemoDatabaseUrl = "",
    [string]$DemoRedisUrl = "redis://redis:6379/0",
    [string]$DemoCeleryBrokerUrl = "redis://redis:6379/1",
    [string]$DemoCeleryResultBackend = "redis://redis:6379/2",
    [string]$FileStorageProvider = "local",
    [string]$AzureStorageConnectionString = "",
    [string]$AzureStorageAccountName = "",
    [string]$AzureStorageAccountKey = "",
    [string]$AzureStorageAccountUrl = "",
    [string]$AzureStorageContainerName = "",
    [string]$AzureStorageContainerUrl = "",
    [string]$SmtpHost = "",
    [string]$SmtpPort = "587",
    [string]$SmtpUsername = "",
    [string]$SmtpPassword = "",
    [string]$EmailFrom = "",
    [string]$SentryDsn = "",
    [string]$SentryRelease = "",
    [string]$SeedDemoData = "true",
    [string]$DemoSkipAttempt = "true",
    [string]$EnableApiDocs = "true",
    [string]$UvicornWorkers = "1"
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' is not available in PATH"
    }
}

function Ensure-LastExitCode {
    param([string]$Action)
    if ($LASTEXITCODE -ne 0) {
        throw "$Action failed with exit code $LASTEXITCODE"
    }
}

Write-Host "[demo-deploy] Starting Azure VM demo deployment from PowerShell"

if ($SecretKey.Length -lt 32) {
    throw "SecretKey must be at least 32 characters"
}

if ([string]::IsNullOrWhiteSpace($FrontendBaseUrl)) {
    $FrontendBaseUrl = "https://$AppDomain"
}
if ([string]::IsNullOrWhiteSpace($CorsOrigins)) {
    $CorsOrigins = $FrontendBaseUrl
}
if ([string]::IsNullOrWhiteSpace($TrustedHosts)) {
    $TrustedHosts = "$AppDomain,localhost,127.0.0.1"
}
if ([string]::IsNullOrWhiteSpace($EmailFrom)) {
    $EmailFrom = "no-reply@$AppDomain"
}
if ([string]::IsNullOrWhiteSpace($DemoDatabaseUrl)) {
    $DemoDatabaseUrl = "postgresql+psycopg2://$PostgresUser`:$PostgresPassword@db:5432/$PostgresDb"
}

Require-Command "git"
Require-Command "ssh"
Require-Command "scp"

if (-not (Test-Path $SshPrivateKeyPath)) {
    throw "SSH private key not found: $SshPrivateKeyPath"
}

$tempRoot = Join-Path $env:TEMP ("lms-demo-deploy-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempRoot | Out-Null

$archivePath = Join-Path $tempRoot "release.tar.gz"
$envPath = Join-Path $tempRoot "deploy.env"
$remoteScriptPath = Join-Path $tempRoot "remote_deploy.sh"

$remoteArchive = "/tmp/lms_backend_demo_release.tar.gz"
$remoteEnv = "/tmp/lms_backend_demo_deploy.env"
$remoteScript = "/tmp/lms_backend_demo_remote_deploy.sh"

try {
    & git archive --format=tar.gz -o $archivePath HEAD
    Ensure-LastExitCode "Creating release archive"

    @"
APP_DIR=$AppDir
APP_DOMAIN=$AppDomain
LETSENCRYPT_EMAIL=$LetsEncryptEmail
SECRET_KEY=$SecretKey
FRONTEND_BASE_URL=$FrontendBaseUrl
CORS_ORIGINS=$CorsOrigins
TRUSTED_HOSTS=$TrustedHosts
POSTGRES_USER=$PostgresUser
POSTGRES_PASSWORD=$PostgresPassword
POSTGRES_DB=$PostgresDb
DEMO_DATABASE_URL=$DemoDatabaseUrl
DEMO_REDIS_URL=$DemoRedisUrl
DEMO_CELERY_BROKER_URL=$DemoCeleryBrokerUrl
DEMO_CELERY_RESULT_BACKEND=$DemoCeleryResultBackend
FILE_STORAGE_PROVIDER=$FileStorageProvider
AZURE_STORAGE_CONNECTION_STRING=$AzureStorageConnectionString
AZURE_STORAGE_ACCOUNT_NAME=$AzureStorageAccountName
AZURE_STORAGE_ACCOUNT_KEY=$AzureStorageAccountKey
AZURE_STORAGE_ACCOUNT_URL=$AzureStorageAccountUrl
AZURE_STORAGE_CONTAINER_NAME=$AzureStorageContainerName
AZURE_STORAGE_CONTAINER_URL=$AzureStorageContainerUrl
SMTP_HOST=$SmtpHost
SMTP_PORT=$SmtpPort
SMTP_USERNAME=$SmtpUsername
SMTP_PASSWORD=$SmtpPassword
EMAIL_FROM=$EmailFrom
SENTRY_DSN=$SentryDsn
SENTRY_RELEASE=$SentryRelease
SEED_DEMO_DATA=$SeedDemoData
DEMO_SKIP_ATTEMPT=$DemoSkipAttempt
ENABLE_API_DOCS=$EnableApiDocs
UVICORN_WORKERS=$UvicornWorkers
"@ | Set-Content -Path $envPath

    $remoteScriptLines = @(
        "#!/usr/bin/env bash"
        "set -euo pipefail"
        "set -a"
        "source /tmp/lms_backend_demo_deploy.env"
        "set +a"
        "mkdir -p ""`$`{APP_DIR`}\"""
        "find ""`$`{APP_DIR`}\"" -mindepth 1 -maxdepth 1 ! -name "".env"" ! -name "".env.demo.azure"" -exec rm -rf {} +"
        "tar -xzf /tmp/lms_backend_demo_release.tar.gz -C ""`$`{APP_DIR`}\"""
        "cd ""`$`{APP_DIR`}\"""
        "chmod +x scripts/platform/linux/deploy_azure_demo_vm.sh"
        "DEPLOY_MODE=vm ./scripts/platform/linux/deploy_azure_demo_vm.sh"
        "rm -f /tmp/lms_backend_demo_release.tar.gz /tmp/lms_backend_demo_deploy.env /tmp/lms_backend_demo_remote_deploy.sh"
    )
    ($remoteScriptLines -join "`n") | Set-Content -Path $remoteScriptPath

    Write-Host "[demo-deploy] Uploading release and deployment metadata"
    & scp -P $SshPort -i $SshPrivateKeyPath -o StrictHostKeyChecking=no $archivePath "${AzureVMUser}@${AzureVMHost}:${remoteArchive}"
    Ensure-LastExitCode "Uploading release archive"

    & scp -P $SshPort -i $SshPrivateKeyPath -o StrictHostKeyChecking=no $envPath "${AzureVMUser}@${AzureVMHost}:${remoteEnv}"
    Ensure-LastExitCode "Uploading deployment env"

    & scp -P $SshPort -i $SshPrivateKeyPath -o StrictHostKeyChecking=no $remoteScriptPath "${AzureVMUser}@${AzureVMHost}:${remoteScript}"
    Ensure-LastExitCode "Uploading remote deployment script"

    Write-Host "[demo-deploy] Executing deployment on VM"
    & ssh -p $SshPort -i $SshPrivateKeyPath -o StrictHostKeyChecking=no "${AzureVMUser}@${AzureVMHost}" "bash ${remoteScript}"
    Ensure-LastExitCode "Remote deployment"

    Write-Host "[demo-deploy] Demo deployment completed successfully"
}
finally {
    if (Test-Path $tempRoot) {
        Remove-Item -Path $tempRoot -Recurse -Force
    }
}
