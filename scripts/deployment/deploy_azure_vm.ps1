# Azure VM Deployment Script for LMS Backend (PowerShell)

param(
    [Parameter(Mandatory = $true)]
    [string]$AzureVMHost,

    [Parameter(Mandatory = $true)]
    [string]$AzureVMUser,

    [Parameter(Mandatory = $true)]
    [string]$ProdDatabaseUrl,

    [Parameter(Mandatory = $true)]
    [string]$SecretKey,

    [Parameter(Mandatory = $true)]
    [string]$AppDomain,

    [Parameter(Mandatory = $true)]
    [string]$LetsEncryptEmail,

    [string]$FrontendBaseUrl,
    [string]$CorsOrigins,
    [string]$TrustedHosts,
    [string]$AppDir = "/opt/lms_backend",
    [string]$SshPrivateKeyPath = "$HOME/.ssh/id_rsa",
    [int]$SshPort = 22,

    [string]$SmtpHost = "",
    [string]$SmtpPort = "587",
    [string]$SmtpUsername = "",
    [string]$SmtpPassword = "",
    [string]$EmailFrom = "",
    [string]$SmtpUseTls = "true",
    [string]$SmtpUseSsl = "false",
    [string]$SentryDsn = "",
    [string]$SentryEnabled = "false",
    [string]$SentryRelease = "",
    [string]$SecretsManagerSource = "env_var",

    [string]$AzureKeyvaultUrl = "",
    [string]$VaultAddr = "",
    [string]$VaultToken = "",
    [string]$VaultNamespace = "",
    [string]$AzureClientId = "",
    [string]$AzureTenantId = "",
    [string]$AzureClientSecret = "",

    [string]$FileStorageProvider = "azure",
    [string]$AzureStorageConnectionString = "",
    [string]$AzureStorageAccountName = "",
    [string]$AzureStorageAccountKey = "",
    [string]$AzureStorageAccountUrl = "",
    [string]$AzureStorageContainerName = "",
    [string]$AzureStorageContainerUrl = ""
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

Write-Host "[deploy] Starting Azure VM deployment from PowerShell"

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
    $TrustedHosts = $AppDomain
}

Require-Command "git"
Require-Command "ssh"
Require-Command "scp"

if (-not (Test-Path $SshPrivateKeyPath)) {
    throw "SSH private key not found: $SshPrivateKeyPath"
}

$tempRoot = Join-Path $env:TEMP ("lms-deploy-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempRoot | Out-Null

$archivePath = Join-Path $tempRoot "release.tar.gz"
$envPath = Join-Path $tempRoot "deploy.env"
$remoteScriptPath = Join-Path $tempRoot "remote_deploy.sh"

$remoteArchive = "/tmp/lms_backend_release.tar.gz"
$remoteEnv = "/tmp/lms_backend_deploy.env"
$remoteScript = "/tmp/lms_backend_remote_deploy.sh"

try {
    & git archive --format=tar.gz -o $archivePath HEAD
    Ensure-LastExitCode "Creating release archive"

    @"
APP_DIR=$AppDir
PROD_DATABASE_URL=$ProdDatabaseUrl
SECRET_KEY=$SecretKey
APP_DOMAIN=$AppDomain
LETSENCRYPT_EMAIL=$LetsEncryptEmail
FRONTEND_BASE_URL=$FrontendBaseUrl
CORS_ORIGINS=$CorsOrigins
TRUSTED_HOSTS=$TrustedHosts
SMTP_HOST=$SmtpHost
SMTP_PORT=$SmtpPort
SMTP_USERNAME=$SmtpUsername
SMTP_PASSWORD=$SmtpPassword
EMAIL_FROM=$EmailFrom
SMTP_USE_TLS=$SmtpUseTls
SMTP_USE_SSL=$SmtpUseSsl
SENTRY_DSN=$SentryDsn
SENTRY_ENABLED=$SentryEnabled
SENTRY_RELEASE=$SentryRelease
SECRETS_MANAGER_SOURCE=$SecretsManagerSource
AZURE_KEYVAULT_URL=$AzureKeyvaultUrl
VAULT_ADDR=$VaultAddr
VAULT_TOKEN=$VaultToken
VAULT_NAMESPACE=$VaultNamespace
AZURE_CLIENT_ID=$AzureClientId
AZURE_TENANT_ID=$AzureTenantId
AZURE_CLIENT_SECRET=$AzureClientSecret
FILE_STORAGE_PROVIDER=$FileStorageProvider
AZURE_STORAGE_CONNECTION_STRING=$AzureStorageConnectionString
AZURE_STORAGE_ACCOUNT_NAME=$AzureStorageAccountName
AZURE_STORAGE_ACCOUNT_KEY=$AzureStorageAccountKey
AZURE_STORAGE_ACCOUNT_URL=$AzureStorageAccountUrl
AZURE_STORAGE_CONTAINER_NAME=$AzureStorageContainerName
AZURE_STORAGE_CONTAINER_URL=$AzureStorageContainerUrl
"@ | Set-Content -Path $envPath

    $remoteScriptLines = @(
        "#!/usr/bin/env bash"
        "set -euo pipefail"
        "sed -i 's/\r$//' /tmp/lms_backend_deploy.env"
        "set -a"
        "source /tmp/lms_backend_deploy.env"
        "set +a"
        "mkdir -p ""`$`{APP_DIR`}"""
        "find ""`$`{APP_DIR`}"" -mindepth 1 -maxdepth 1 ! -name "".env"" -exec rm -rf {} +"
        "tar -xzf /tmp/lms_backend_release.tar.gz -C ""`$`{APP_DIR`}"""
        "cd ""`$`{APP_DIR`}"""
        "sed -i 's/\r$//' scripts/platform/linux/deploy_azure_vm.sh"
        "chmod +x scripts/platform/linux/deploy_azure_vm.sh"
        "DEPLOY_MODE=vm bash ./scripts/platform/linux/deploy_azure_vm.sh"
        "rm -f /tmp/lms_backend_release.tar.gz /tmp/lms_backend_deploy.env /tmp/lms_backend_remote_deploy.sh"
    )
    $remoteScriptContent = ($remoteScriptLines -join "`n") + "`n"
    [System.IO.File]::WriteAllText(
        $remoteScriptPath,
        $remoteScriptContent,
        [System.Text.UTF8Encoding]::new($false)
    )

    Write-Host "[deploy] Uploading release and deployment metadata"
    & scp -P $SshPort -i $SshPrivateKeyPath -o StrictHostKeyChecking=no $archivePath "${AzureVMUser}@${AzureVMHost}:${remoteArchive}"
    Ensure-LastExitCode "Uploading release archive"

    & scp -P $SshPort -i $SshPrivateKeyPath -o StrictHostKeyChecking=no $envPath "${AzureVMUser}@${AzureVMHost}:${remoteEnv}"
    Ensure-LastExitCode "Uploading deployment env"

    & scp -P $SshPort -i $SshPrivateKeyPath -o StrictHostKeyChecking=no $remoteScriptPath "${AzureVMUser}@${AzureVMHost}:${remoteScript}"
    Ensure-LastExitCode "Uploading remote deployment script"

    Write-Host "[deploy] Executing deployment on VM"
    & ssh -p $SshPort -i $SshPrivateKeyPath -o StrictHostKeyChecking=no "${AzureVMUser}@${AzureVMHost}" "bash ${remoteScript}"
    Ensure-LastExitCode "Remote deployment"

    Write-Host "[deploy] Deployment completed successfully"
}
finally {
    if (Test-Path $tempRoot) {
        Remove-Item -Path $tempRoot -Recurse -Force
    }
}
