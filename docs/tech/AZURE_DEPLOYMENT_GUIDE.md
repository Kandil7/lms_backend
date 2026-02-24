# Azure Deployment Guide for LMS Backend

This comprehensive guide covers deploying the LMS Backend application to Microsoft Azure using multiple deployment options. The project includes built-in support for Azure VM deployment with Docker Compose, Azure Container Apps for serverless deployments, and AKS for Kubernetes-based deployments.

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Architecture Overview](#2-architecture-overview)
3. [Option 1: Azure VM Deployment](#3-option-1-azure-vm-deployment)
4. [Option 2: Azure Container Apps](#4-option-2-azure-container-apps)
5. [Option 3: Azure Kubernetes Service](#5-option-3-azure-kubernetes-service-aks)
6. [Environment Variables Reference](#6-environment-variables-reference)
7. [Post-Deployment Verification](#7-post-deployment-verification)
8. [Troubleshooting Common Issues](#8-troubleshooting-common-issues)
9. [Security Considerations](#9-security-considerations)
10. [Monitoring and Observability](#10-monitoring-and-observability)
11. [Database Backup Configuration](#11-database-backup-configuration)

---

## 1. Prerequisites

Before deploying to Azure, ensure you have the following prerequisites in place.

### 1.1 Azure Account and Subscription

You need an active Azure subscription with sufficient permissions to create resources. If you don't have an account, create one at [azure.com](https://azure.com).

```bash
# Verify Azure CLI is installed and authenticated
az login

# Show current subscription
az account show

# List available subscriptions if needed
az account list --output table
```

### 1.2 Azure CLI Installation

Install the Azure CLI on your local machine:

```bash
# Windows (using winget)
winget install Microsoft.AzureCLI

# macOS (using Homebrew)
brew install azure-cli

# Linux (Ubuntu/Debian)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

Verify the installation:

```bash
az --version
```

### 1.3 Required Tools

Ensure the following tools are installed:

| Tool | Purpose | Installation |
|------|---------|--------------|
| Git | Version control | `brew install git` (macOS) or download from git-scm.com |
| Docker | Container runtime | docker.com/get-docker |
| Docker Compose | Container orchestration | Included with Docker Desktop |
| SSH | Remote server access | Included with Git Bash or download from OpenSSH |

### 1.4 SSH Key Generation

Generate an SSH key pair for VM access:

```bash
# Generate SSH key pair (if you don't have one)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Add to SSH agent (Linux/macOS/WSL)
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
```

### 1.5 Resource Group Creation

Create a resource group to organize your Azure resources:

```bash
# Variables
RESOURCE_GROUP="lms-backend-rg"
LOCATION="eastus"

# Create resource group
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION"
```

---

## 2. Architecture Overview

The LMS Backend can be deployed to Azure using three different approaches:

### 2.1 Option Comparison

| Feature | Azure VM | Azure Container Apps | AKS |
|---------|----------|---------------------|-----|
| Complexity | Low | Medium | High |
| Cost | Fixed hourly | Pay-per-use | Cluster minimum |
| Scalability | Manual/VM scale | Auto-scale | Auto-scale |
| Maintenance | You manage | Azure manages | You manage |
| Best for | Full control | Serverless/simple | Kubernetes teams |

### 2.2 Component Architecture

All deployment options use the same application architecture:

```
                                    +------------------+
                                    |   Caddy (TLS)   |
                                    |   Port 80/443   |
                                    +--------+--------+
                                             |
                                    +--------v--------+
                                    |    API Server   |
                                    |   FastAPI/Uvicorn|
                                    |    Port 8000    |
                                    +--------+--------+
                                             |
        +------------------+-----------------+------------------+
        |                  |                  |                  |
+-------+-------+  +-------+-------+  +------+-------+  +-------+-------+
|  Celery   |  |  Celery   |  |  PostgreSQL  |  |  Redis     |  |  Azure    |
|  Worker   |  |  Beat     |  |  (Azure DB)  |  |  (Cache)   |  |  Blob     |
+-----------+  +-----------+  +--------------+  +------------+  +-----------+
```

---

## 3. Option 1: Azure VM Deployment

This is the most common and recommended approach for production deployments requiring full control.

### 3.1 Create Azure VM

#### 3.1.1 Create Virtual Network and Subnet

```bash
# Variables
RESOURCE_GROUP="lms-backend-rg"
VNET_NAME="lms-backend-vnet"
SUBNET_NAME="lms-backend-subnet"
LOCATION="eastus"

# Create virtual network
az network vnet create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$VNET_NAME" \
  --address-prefixes 10.0.0.0/16 \
  --subnet-name "$SUBNET_NAME" \
  --subnet-prefixes 10.0.1.0/24
```

#### 3.1.2 Create Network Security Group

```bash
# Create NSG
az network nsg create \
  --resource-group "$RESOURCE_GROUP" \
  --name "lms-backend-nsg"

# Allow SSH (restrict to your IP for production)
az network nsg rule create \
  --resource-group "$RESOURCE_GROUP" \
  --nsg-name "lms-backend-nsg" \
  --name "allow-ssh" \
  --priority 100 \
  --source-address-prefixes "YOUR_IP_ADDRESS/32" \
  --source-port-ranges "*" \
  --destination-address-prefixes "*" \
  --destination-port-ranges "22" \
  --access "Allow" \
  --protocol "Tcp"

# Allow HTTP (for Let's Encrypt)
az network nsg rule create \
  --resource-group "$RESOURCE_GROUP" \
  --nsg-name "lms-backend-nsg" \
  --name "allow-http" \
  --priority 110 \
  --source-address-prefixes "*" \
  --source-port-ranges "*" \
  --destination-address-prefixes "*" \
  --destination-port-ranges "80" \
  --access "Allow" \
  --protocol "Tcp"

# Allow HTTPS
az network nsg rule create \
  --resource-group "$RESOURCE_GROUP" \
  --nsg-name "lms-backend-nsg" \
  --name "allow-https" \
  --priority 120 \
  --source-address-prefixes "*" \
  --source-port-ranges "*" \
  --destination-address-prefixes "*" \
  --destination-port-ranges "443" \
  --access "Allow" \
  --protocol "Tcp"
```

#### 3.1.3 Create Public IP Address

```bash
# Create public IP
az network public-ip create \
  --resource-group "$RESOURCE_GROUP" \
  --name "lms-backend-pip" \
  --allocation-method "Static" \
  --sku "Standard"

# Get the public IP
VM_PUBLIC_IP=$(az network public-ip show \
  --resource-group "$RESOURCE_GROUP" \
  --name "lms-backend-pip" \
  --query "ipAddress" \
  --output tsv)

echo "VM Public IP: $VM_PUBLIC_IP"
```

#### 3.1.4 Create the VM

```bash
# VM variables
VM_NAME="lms-backend-vm"
VM_SIZE="Standard_D2s_v3"
ADMIN_USERNAME="azureuser"
SSH_PUBLIC_KEY_PATH="~/.ssh/id_rsa.pub"

# Create VM
az vm create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$VM_NAME" \
  --size "$VM_SIZE" \
  --image "UbuntuLTS" \
  --admin-username "$ADMIN_USERNAME" \
  --ssh-key-value "$SSH_PUBLIC_KEY_PATH" \
  --vnet-name "$VNET_NAME" \
  --subnet "$SUBNET_NAME" \
  --public-ip-address "lms-backend-pip" \
  --nsg "lms-backend-nsg" \
  --boot-diagnostics-storage "lmsbackenddiag" \
  --priority "Regular"

# Note: For boot diagnostics, create a storage account first if needed
# az storage account create --name lmsbackenddiag --resource-group $RESOURCE_GROUP --sku Standard_LRS
```

### 3.2 Install Docker and Docker Compose on VM

Connect to your VM and install Docker:

```bash
# Connect to VM
SSH_USER="azureuser"
VM_IP="your-vm-public-ip"

ssh "$SSH_USER@$VM_IP"
```

Once connected, run the following commands:

```bash
# Update package index
sudo apt update
sudo apt upgrade -y

# Install dependencies
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Start and enable Docker
sudo systemctl enable docker
sudo systemctl start docker

# Verify Docker installation
docker --version
docker compose version
```

### 3.3 Configure Azure Database for PostgreSQL

#### 3.3.1 Create Azure Database for PostgreSQL Flexible Server

```bash
# Variables
DB_SERVER_NAME="lms-backend-db"
DB_ADMIN_USER="lmsadmin"
DB_ADMIN_PASSWORD="YourSecurePassword123!"
DB_NAME="lms"

# Create PostgreSQL flexible server
az postgres flexible-server create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DB_SERVER_NAME" \
  --location "$LOCATION" \
  --sku-name "Standard_D2s_v3" \
  --tier "GeneralPurpose" \
  --version "16" \
  --admin-user "$DB_ADMIN_USER" \
  --admin-password "$DB_ADMIN_PASSWORD" \
  --storage-size "128" \
  --high-availability "ZoneRedundant" \
  --backup-retention "7" \
  --geo-redundant-backup "Enabled"

# Create database
az postgres flexible-server db create \
  --resource-group "$RESOURCE_GROUP" \
  --server-name "$DB_SERVER_NAME" \
  --database-name "$DB_NAME"
```

#### 3.3.2 Configure Firewall Rules

```bash
# Get your VM's public IP
VM_PUBLIC_IP=$(az vm get-instance-view \
  --name "$VM_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "publicIps" \
  --output tsv)

# Allow VM to connect to database
az postgres flexible-server firewall-rule create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DB_SERVER_NAME" \
  --rule-name "allow-lms-vm" \
  --start-ip-address "$VM_PUBLIC_IP" \
  --end-ip-address "$VM_PUBLIC_IP"

# Allow Azure services (optional, for Azure resources)
az postgres flexible-server firewall-rule create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DB_SERVER_NAME" \
  --rule-name "allow-azure-services" \
  --start-ip-address "0.0.0.0" \
  --end-ip-address "0.0.0.0"
```

#### 3.3.3 Get Database Connection String

```bash
# Get the full connection string
DB_HOST="$DB_SERVER_NAME.postgres.database.azure.com"
DB_PORT="5432"

# Your connection string will be:
# postgresql+psycopg2://lmsadmin:YourSecurePassword123!@lms-backend-db.postgres.database.azure.com:5432/lms?sslmode=require

echo "Database Host: $DB_HOST"
echo "Database Port: $DB_PORT"
echo "Connection: postgresql+psycopg2://$DB_ADMIN_USER:<password>@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require"
```

### 3.4 Configure Azure Blob Storage (Optional)

Azure Blob Storage is used for storing uploaded files (videos, documents, certificates).

#### 3.4.1 Create Storage Account

```bash
# Variables
STORAGE_ACCOUNT_NAME="lmsbackendstorage"
STORAGE_CONTAINER_NAME="lms-files"

# Create storage account
az storage account create \
  --name "$STORAGE_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku "Standard_LRS" \
  --kind "StorageV2"

# Get storage account keys
az storage account keys list \
  --resource-group "$RESOURCE_GROUP" \
  --account-name "$STORAGE_ACCOUNT_NAME"

# Create blob container
az storage container create \
  --name "$STORAGE_CONTAINER_NAME" \
  --account-name "$STORAGE_ACCOUNT_NAME" \
  --public-access "off"

# Set CORS (if needed for direct uploads)
az storage cors show \
  --account-name "$STORAGE_ACCOUNT_NAME" \
  --services b
```

#### 3.4.2 Configure CORS for the Container

```bash
# Allow CORS for frontend applications
az storage cors clear \
  --account-name "$STORAGE_ACCOUNT_NAME" \
  --services b

# Set CORS rules (example for development)
az storage cors add \
  --account-name "$STORAGE_ACCOUNT_NAME" \
  --services b \
  --allowed-methods "GET,PUT,HEAD" \
  --allowed-origins "https://your-frontend.com" \
  --allowed-headers "*" \
  --max-age 3600
```

### 3.5 Set Up DNS

#### 3.5.1 Configure DNS Zone

If you already have a domain, create a DNS zone in Azure:

```bash
# Create DNS zone
az network dns zone create \
  --resource-group "$RESOURCE_GROUP" \
  --name "yourdomain.com"

# Get nameservers
az network dns zone show \
  --resource-group "$RESOURCE_GROUP" \
  --name "yourdomain.com" \
  --query "nameServers"
```

Update your domain registrar's nameservers to point to Azure DNS.

#### 3.5.2 Create DNS Records

```bash
# Get VM public IP
VM_PUBLIC_IP=$(az network public-ip show \
  --resource-group "$RESOURCE_GROUP" \
  --name "lms-backend-pip" \
  --query "ipAddress" \
  --output tsv)

# Create A record for API
az network dns record-set a create \
  --resource-group "$RESOURCE_GROUP" \
  --zone-name "yourdomain.com" \
  --name "api" \
  --ttl 300

az network dns record-set a add-record \
  --resource-group "$RESOURCE_GROUP" \
  --zone-name "yourdomain.com" \
  --record-set-name "api" \
  --ipv4-address "$VM_PUBLIC_IP"

# Optionally create CNAME for www or bare domain
az network dns record-set cname create \
  --resource-group "$RESOURCE_GROUP" \
  --zone-name "yourdomain.com" \
  --name "www" \
  --ttl 300

az network dns record-set cname set-record \
  --resource-group "$RESOURCE_GROUP" \
  --zone-name "yourdomain.com" \
  --record-set-name "www" \
  --cname "api.yourdomain.com"
```

### 3.6 Deploy the Application

#### 3.6.1 Manual Deployment

Connect to your VM and run the deployment:

```bash
# SSH into VM
ssh azureuser@your-vm-ip

# Clone the repository (or use the deployment scripts)
cd /opt
sudo mkdir -p lms_backend
sudo chown $USER:$USER lms_backend
cd lms_backend

# Clone your repository
git clone https://github.com/your-org/lms_backend.git .

# Create production environment file
cp .env.demo.azure.example .env

# Edit the .env file with your configuration
nano .env
```

Create your production `.env` file with these essential variables:

```bash
# Production Environment Variables
cat > .env << 'EOF'
# Database (Azure PostgreSQL)
PROD_DATABASE_URL=postgresql+psycopg2://lmsadmin:YourSecurePassword123!@lms-backend-db.postgres.database.azure.com:5432/lms?sslmode=require

# Redis
PROD_REDIS_URL=redis://redis:6379/0
PROD_CELERY_BROKER_URL=redis://redis:6379/1
PROD_CELERY_RESULT_BACKEND=redis://redis:6379/2

# Security
SECRET_KEY=your-32-character-minimum-secret-key-here

# Domain / TLS
APP_DOMAIN=api.yourdomain.com
LETSENCRYPT_EMAIL=ops@yourdomain.com

# Frontend / CORS
FRONTEND_BASE_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com
TRUSTED_HOSTS=api.yourdomain.com,localhost,127.0.0.1

# SMTP (optional)
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USERNAME=resend
SMTP_PASSWORD=your-resend-api-key
EMAIL_FROM=noreply@yourdomain.com
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# Monitoring (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production

# Azure Storage (optional)
FILE_STORAGE_PROVIDER=azure
AZURE_STORAGE_CONNECTION_STRING=your-azure-storage-connection-string
AZURE_STORAGE_ACCOUNT_NAME=lmsbackendstorage
AZURE_STORAGE_CONTAINER_NAME=lms-files
EOF
```

Run the deployment script:

```bash
# Make deployment script executable
chmod +x scripts/platform/linux/deploy_azure_vm.sh

# Run deployment
APP_DIR=/opt/lms_backend DEPLOY_MODE=vm ./scripts/platform/linux/deploy_azure_vm.sh
```

#### 3.6.2 GitHub Actions Deployment (Recommended)

Configure GitHub Actions for automated deployments:

##### Step 1: Create GitHub Repository Secrets

Navigate to your repository settings: `Settings > Secrets and variables > Actions`

Add the following secrets:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AZURE_VM_HOST` | VM public IP or hostname | `api.yourdomain.com` |
| `AZURE_VM_USER` | SSH username | `azureuser` |
| `AZURE_VM_SSH_KEY` | Private SSH key content | (Paste private key) |
| `PROD_DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://...` |
| `SECRET_KEY` | Application secret key | (32+ character random string) |
| `APP_DOMAIN` | Your API domain | `api.yourdomain.com` |
| `LETSENCRYPT_EMAIL` | Email for Let's Encrypt | `ops@yourdomain.com` |
| `FRONTEND_BASE_URL` | Frontend URL | `https://yourdomain.com` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://yourdomain.com` |
| `TRUSTED_HOSTS` | Trusted hosts | `api.yourdomain.com,localhost` |
| `SMTP_HOST` | SMTP server | `smtp.resend.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USERNAME` | SMTP username | `resend` |
| `SMTP_PASSWORD` | SMTP password/API key | (Your API key) |
| `EMAIL_FROM` | From email address | `noreply@yourdomain.com` |
| `SENTRY_DSN` | Sentry DSN | `https://...@sentry.io/...` |

##### Step 2: Configure GitHub Environment

1. Go to `Settings > Environments`
2. Create a `production` environment
3. Add protection rules (optional):
   - Required reviewers
   - Wait timer
   - Deployment branches (main)

##### Step 3: Deploy

Push to the main branch or manually trigger the workflow:

```bash
# Push to main branch to trigger deployment
git push origin main

# Or trigger manually via GitHub UI
# Navigate to Actions > Deploy Azure VM > Run workflow
```

---

## 4. Option 2: Azure Container Apps

Azure Container Apps provides a serverless container platform suitable for smaller deployments.

### 4.1 Prerequisites

```bash
# Enable Container Apps extension
az extension add --name containerapp
```

### 4.2 Create Container Apps Environment

```bash
# Variables
CONTAINERAPPS_ENV="lms-backend-env"
LOG_ANALYTICS_WORKSPACE="lms-backend-law"

# Create log analytics workspace
az monitor log-analytics workspace create \
  --resource-group "$RESOURCE_GROUP" \
  --workspace-name "$LOG_ANALYTICS_WORKSPACE"

LOG_ANALYTICS_ID=$(az monitor log-analytics workspace show \
  --resource-group "$RESOURCE_GROUP" \
  --workspace-name "$LOG_ANALYTICS_WORKSPACE" \
  --query "customerId" \
  --output tsv)

LOG_ANALYTICS_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group "$RESOURCE_GROUP" \
  --workspace-name "$LOG_ANALYTICS_WORKSPACE" \
  --query "primarySharedKey" \
  --output tsv)

# Create Container Apps environment
az containerapp env create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CONTAINERAPPS_ENV" \
  --location "$LOCATION"
```

### 4.3 Create Container Apps

#### 4.3.1 Create API Container App

```bash
# Variables
API_IMAGE="your-registry.azurecr.io/lms-backend-api:latest"
API_APP_NAME="lms-backend-api"

# Create API container app
az containerapp create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$API_APP_NAME" \
  --environment "$CONTAINERAPPS_ENV" \
  --image "$API_IMAGE" \
  --target-port 8000 \
  --ingress external \
  --cpu 1.0 --memory 2Gi \
  --min-replicas 1 --max-replicas 5 \
  --scale-rule-name "http-scaling" \
  --scale-rule-type "http" \
  --scale-rule-metadata "concurrentRequests=10" \
  --env-vars \
    "ENVIRONMENT=production" \
    "DEBUG=false" \
    "PROD_DATABASE_URL=$PROD_DATABASE_URL" \
    "SECRET_KEY=$SECRET_KEY" \
    "APP_DOMAIN=$APP_DOMAIN"
```

#### 4.3.2 Create Redis (Using Azure Cache for Redis)

```bash
# Create Azure Cache for Redis
az redis create \
  --resource-group "$RESOURCE_GROUP" \
  --name "lms-backend-redis" \
  --sku "Standard" \
  --vm-size "C0"
```

### 4.4 Configure Ingress and TLS

```bash
# Enable TLS for the API
az containerapp ingress show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$API_APP_NAME"

# Update to use custom domain (requires certificate)
az containerapp ingress custom-domain update \
  --resource-group "$RESOURCE_GROUP" \
  --name "$API_APP_NAME" \
  --domain "api.yourdomain.com" \
  --certificate-arm "/subscriptions/.../certificate-arn"
```

### 4.5 Database Migration

Run migrations using a one-time container job:

```bash
# Create migration job
az containerapp job create \
  --resource-group "$RESOURCE_GROUP" \
  --name "lms-migrate" \
  --image "$API_IMAGE" \
  --command "python scripts/database/wait_for_db.py && alembic upgrade head" \
  --env-vars \
    "DATABASE_URL=$PROD_DATABASE_URL" \
    "ENVIRONMENT=production" \
  --trigger-type "Manual"
```

---

## 5. Option 3: Azure Kubernetes Service (AKS)

AKS provides full Kubernetes control for teams with Kubernetes expertise.

### 5.1 Create AKS Cluster

```bash
# Variables
AKS_CLUSTER_NAME="lms-backend-aks"
AKS_NODE_COUNT=2
AKS_VM_SIZE="Standard_D2s_v3"

# Create AKS cluster
az aks create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$AKS_CLUSTER_NAME" \
  --node-count "$AKS_NODE_COUNT" \
  --vm-set-type "VirtualMachineScaleSets" \
  --load-balancer-sku "standard" \
  --enable-addons "monitoring" \
  --enable-msi-auth-for-monitoring true \
  --generate-ssh-keys

# Get credentials
az aks get-credentials \
  --resource-group "$RESOURCE_GROUP" \
  --name "$AKS_CLUSTER_NAME" \
  --overwrite-existing
```

### 5.2 Create Kubernetes Manifests

Create a `kubernetes/` directory with deployment manifests:

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lms-backend-api
  namespace: lms
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lms-backend-api
  template:
    metadata:
      labels:
        app: lms-backend-api
    spec:
      containers:
      - name: api
        image: your-registry.azurecr.io/lms-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: lms-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: lms-secrets
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: lms-backend-api
  namespace: lms
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: lms-backend-api
```

```yaml
# kubernetes/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: lms-backend-ingress
  namespace: lms
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: lms-backend-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: lms-backend-api
            port:
              number: 80
```

```yaml
# kubernetes/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: lms-secrets
  namespace: lms
type: Opaque
stringData:
  database-url: "postgresql+psycopg2://..."
  secret-key: "your-32-char-secret"
```

### 5.3 Deploy to AKS

```bash
# Create namespace
kubectl create namespace lms

# Apply secrets (keep outside of version control)
kubectl apply -f kubernetes/secrets.yaml

# Apply deployment
kubectl apply -f kubernetes/deployment.yaml

# Apply ingress
kubectl apply -f kubernetes/ingress.yaml

# Check deployment status
kubectl get pods -n lms
kubectl get services -n lms
kubectl get ingress -n lms
```

### 5.4 Set Up Horizontal Pod Autoscaler

```bash
# Install metrics server (if not already installed)
az aks enable-addons \
  --resource-group "$RESOURCE_GROUP" \
  --name "$AKS_CLUSTER_NAME" \
  --addons azure-keyvault-secrets-provider

# Create HPA
kubectl autoscale deployment lms-backend-api \
  --namespace lms \
  --cpu-percent=70 \
  --min=2 \
  --max=10
```

---

## 6. Environment Variables Reference

### 6.1 Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PROD_DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://user:pass@host:5432/db?sslmode=require` |
| `SECRET_KEY` | Application secret (min 32 chars) | `your-32-character-secret-key-here` |
| `APP_DOMAIN` | Production domain | `api.yourdomain.com` |
| `LETSENCRYPT_EMAIL` | Email for TLS certificates | `ops@yourdomain.com` |

### 6.2 Database Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROD_DATABASE_URL` | - | Full database connection string |
| `POSTGRES_USER` | `lms` | PostgreSQL username |
| `POSTGRES_PASSWORD` | - | PostgreSQL password |
| `POSTGRES_DB` | `lms` | Database name |
| `DB_POOL_SIZE` | `20` | Database connection pool size |
| `DB_MAX_OVERFLOW` | `40` | Max overflow connections |
| `SQLALCHEMY_ECHO` | `false` | Log SQL queries |

### 6.3 Redis/Celery Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROD_REDIS_URL` | `redis://redis:6379/0` | Redis connection for caching |
| `PROD_CELERY_BROKER_URL` | `redis://redis:6379/1` | Celery message broker |
| `PROD_CELERY_RESULT_BACKEND` | `redis://redis:6379/2` | Celery results store |

### 6.4 Security Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token expiry |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token expiry |
| `ACCESS_TOKEN_BLACKLIST_ENABLED` | `true` | Enable token blacklist |
| `MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES` | `10` | MFA challenge expiry |

### 6.5 Email/SMTP Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | - | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USERNAME` | - | SMTP username |
| `SMTP_PASSWORD` | - | SMTP password |
| `EMAIL_FROM` | - | From email address |
| `SMTP_USE_TLS` | `true` | Use TLS connection |
| `SMTP_USE_SSL` | `false` | Use SSL connection |

### 6.6 Azure Storage Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FILE_STORAGE_PROVIDER` | `azure` | Storage provider (`local` or `azure`) |
| `AZURE_STORAGE_CONNECTION_STRING` | - | Azure storage connection string |
| `AZURE_STORAGE_ACCOUNT_NAME` | - | Storage account name |
| `AZURE_STORAGE_ACCOUNT_KEY` | - | Storage account key |
| `AZURE_STORAGE_CONTAINER_NAME` | - | Blob container name |

### 6.7 Monitoring Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SENTRY_DSN` | - | Sentry DSN URL |
| `SENTRY_ENVIRONMENT` | `production` | Sentry environment |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Trace sampling rate |
| `METRICS_ENABLED` | `true` | Enable Prometheus metrics |
| `METRICS_PATH` | `/metrics` | Metrics endpoint path |

---

## 7. Post-Deployment Verification

### 7.1 Health Check Endpoints

Verify the application is running correctly:

```bash
# Test readiness endpoint
curl -f https://api.yourdomain.com/api/v1/ready

# Test health endpoint
curl -f https://api.yourdomain.com/api/v1/health

# Test metrics endpoint (if enabled)
curl -f https://api.yourdomain.com/metrics

# Test OpenAPI docs (if enabled)
curl -f https://api.yourdomain.com/docs
```

Expected responses:

```json
// /api/v1/ready
{
  "status": "ready",
  "database": "connected",
  "redis": "connected"
}

// /api/v1/health
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 7.2 Docker Compose Status

```bash
# Check container status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f api

# Check resource usage
docker stats
```

### 7.3 Test Authentication

```bash
# Test login endpoint
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpassword"}'
```

### 7.4 Test File Upload (if configured)

```bash
# Create test file
echo "test content" > test.txt

# Upload file
curl -X POST https://api.yourdomain.com/api/v1/files/upload \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@test.txt"
```

---

## 8. Troubleshooting Common Issues

### 8.1 Container Issues

#### Container Won't Start

```bash
# Check container logs
docker compose -f docker-compose.prod.yml logs api

# Check if port is already in use
sudo netstat -tulpn | grep 8000

# Check environment variables
docker compose -f docker-compose.prod.yml config
```

#### Database Connection Failed

```bash
# Test database connectivity from container
docker compose -f docker-compose.prod.yml exec api python -c "
import psycopg2
try:
    conn = psycopg2.connect('$PROD_DATABASE_URL')
    print('Database connected successfully')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"

# Check PostgreSQL firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group "$RESOURCE_GROUP" \
  --server-name "$DB_SERVER_NAME"
```

### 8.2 TLS/SSL Issues

#### Let's Encrypt Certificate Not Issuing

```bash
# Check Caddy logs
docker compose -f docker-compose.prod.yml logs caddy

# Verify DNS is pointing correctly
nslookup api.yourdomain.com

# Test HTTP port is accessible
curl -v http://api.yourdomain.com

# Check NSG allows port 80
az network nsg rule show \
  --resource-group "$RESOURCE_GROUP" \
  --nsg-name "lms-backend-nsg" \
  --name "allow-http"
```

#### Certificate Expiring

```bash
# Force certificate renewal
docker compose -f docker-compose.prod.yml exec caddy caddy reload --config /etc/caddy/Caddyfile

# Or restart Caddy
docker compose -f docker-compose.prod.yml restart caddy
```

### 8.3 Performance Issues

#### High Memory Usage

```bash
# Check container memory usage
docker stats

# Adjust memory limits in docker-compose.prod.yml
# Increase UVICORN_WORKERS if CPU-bound
```

#### Slow Database Queries

```bash
# Enable query logging
SQLALCHEMY_ECHO=true docker compose -f docker-compose.prod.yml up -d

# Check for slow queries in logs
docker compose -f docker-compose.prod.yml logs api | grep "slow"
```

### 8.4 Network Issues

#### Cannot Connect to VM via SSH

```bash
# Check NSG rules
az network nsg rule list \
  --resource-group "$RESOURCE_GROUP" \
  --nsg-name "lms-backend-nsg" \
  --output table

# Test SSH connectivity
ssh -v azureuser@your-vm-ip
```

#### Cannot Access Application

```bash
# Check if containers are running
docker compose -f docker-compose.prod.yml ps

# Check if ports are listening
sudo netstat -tulpn | grep -E "80|443|8000"

# Verify firewall on VM
sudo ufw status
sudo iptables -L -n
```

### 8.5 Azure-Specific Issues

#### Outbound IP Not Whitelisted

```bash
# Get VM's current public IP
az vm show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$VM_NAME" \
  --query "publicIps"

# Update database firewall rule
az postgres flexible-server firewall-rule update \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DB_SERVER_NAME" \
  --rule-name "allow-lms-vm" \
  --start-ip-address "$NEW_IP" \
  --end-ip-address "$NEW_IP"
```

---

## 9. Security Considerations

### 9.1 VM Security

```bash
# Disable password authentication
sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Configure fail2ban (optional)
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
```

### 9.2 Database Security

```bash
# Enable SSL for PostgreSQL connection
# This is already configured via ?sslmode=require in the connection string

# Create read-only database user for application
az postgres flexible-server execute \
  --resource-group "$RESOURCE_GROUP" \
  --server-name "$DB_SERVER_NAME" \
  --name "lms" \
  --query-text "
    CREATE USER lms_readonly WITH PASSWORD 'strong_password';
    GRANT CONNECT ON DATABASE lms TO lms_readonly;
    GRANT USAGE ON SCHEMA public TO lms_readonly;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO lms_readonly;
  "
```

### 9.3 Secrets Management

Use Azure Key Vault for production secrets:

```bash
# Create Key Vault
az keyvault create \
  --resource-group "$RESOURCE_GROUP" \
  --name "lms-backend-kv"

# Store secrets
az keyvault secret set \
  --vault-name "lms-backend-kv" \
  --name "database-url" \
  --value "postgresql+psycopg2://..."

az keyvault secret set \
  --vault-name "lms-backend-kv" \
  --name "secret-key" \
  --value "your-secret-key"

# Enable Key Vault in deployment
# Update .env or deployment scripts to use Key Vault references
```

---

## 10. Monitoring and Observability

### 10.1 Sentry Integration

Sentry is already configured in the application. Set up your Sentry project:

1. Create account at [sentry.io](https://sentry.io)
2. Create new project for LMS Backend
3. Copy DSN and add to secrets

```bash
# In your environment or secrets
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 10.2 Application Insights (Optional)

```bash
# Create Application Insights
az monitor app-insights component create \
  --app "lms-backend-insights" \
  --location "$LOCATION" \
  --resource-group "$RESOURCE_GROUP"

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app "lms-backend-insights" \
  --resource-group "$RESOURCE_GROUP" \
  --query "instrumentationKey" \
  --output tsv)

# Add to application
# Set APPLICATIONINSIGHTS_CONNECTION_STRING in your environment
```

### 10.3 Log Analytics

```bash
# Query logs from Azure Portal or CLI
az monitor log-analytics query \
  --workspace "$LOG_ANALYTICS_WORKSPACE" \
  --analytics-query "ContainerLog | where ContainerName contains 'lms-backend' | take 100"
```

---

## 11. Database Backup Configuration

### 11.1 Azure PostgreSQL Backups

Azure Database for PostgreSQL Flexible Server includes automatic backups:

```bash
# Check backup configuration
az postgres flexible-server show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DB_SERVER_NAME" \
  --query "backup"

# Restore from backup (point-in-time recovery)
az postgres flexible-server restore \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DB_SERVER_NAME-restored" \
  --source-server "$DB_SERVER_NAME" \
  --restore-point-timestamp "2024-01-15T10:00:00Z"
```

### 11.2 Manual Database Backup

```bash
# Create manual backup
BACKUP_NAME="lms-backup-$(date +%Y%m%d)"

# Export database using pg_dump
docker run --rm \
  -e PGPASSWORD="$DB_PASSWORD" \
  -v $(pwd):/backup \
  postgres:16 \
  pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
  -F c -b -v -f "/backup/$BACKUP_NAME.dump"

# Verify backup
docker run --rm \
  -v $(pwd):/backup \
  postgres:16 \
  pg_restore --list "/backup/$BACKUP_NAME.dump"
```

### 11.3 Configure Backup Schedule

```bash
# Create automation account
az automation account create \
  --resource-group "$RESOURCE_GROUP" \
  --name "lms-backend-automation" \
  --location "$LOCATION"

# Create runbook for scheduled backups
# This would be configured in Azure Automation or use Azure Functions
```

---

## Quick Reference

### Essential Commands

```bash
# SSH to VM
ssh azureuser@api.yourdomain.com

# Check application status
docker compose -f /opt/lms_backend/docker-compose.prod.yml ps

# View application logs
docker compose -f /opt/lms_backend/docker-compose.prod.yml logs -f api

# Restart application
docker compose -f /opt/lms_backend/docker-compose.prod.yml restart

# Reload after .env changes
docker compose -f /opt/lms_backend/docker-compose.prod.yml up -d

# Manual deployment (from VM)
/opt/lms_backend/scripts/platform/linux/deploy_azure_vm.sh
```

### Important Ports

| Port | Service | Description |
|------|---------|-------------|
| 22 | SSH | Remote access |
| 80 | HTTP | Let's Encrypt ACME challenge |
| 443 | HTTPS | Production traffic |
| 6379 | Redis | Redis (internal) |
| 5432 | PostgreSQL | Database (internal) |

---

## Related Documentation

- [Azure Production Deployment](./ops/10-azure-production-deployment.md) - Basic deployment overview
- [Security Hardening Guide](./ops/12-server-hardening-guide.md) - Server hardening steps
- [TLS Termination Guide](./ops/11-tls-termination-guide.md) - SSL/TLS configuration
- [Sentry Configuration Guide](./ops/14-sentry-configuration-guide.md) - Monitoring setup
- [Secrets Management Guide](./ops/24-secrets-management-guide.md) - Azure Key Vault integration
- [Azure Key Vault Integration](./ops/25-azure-key-vault-integration.md) - Key Vault setup
