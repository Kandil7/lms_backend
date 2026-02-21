# Azure Production Deployment (VM + Caddy + Azure PostgreSQL)

## Architecture
- App runtime: Azure VM (`docker-compose.prod.yml`)
- TLS + reverse proxy: Caddy (`80/443`)
- Database: Azure Database for PostgreSQL Flexible Server (managed backups + HA)
- Cache/queue: Redis container on VM

## 1. DNS and TLS
1. Create an `A` record for your API domain pointing to VM public IP.
2. Set `.env` values on VM:
   - `APP_DOMAIN=api.example.com`
   - `LETSENCRYPT_EMAIL=ops@example.com`
3. Open NSG inbound ports `80` and `443`.
4. Deploy stack:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```
5. Verify:
   ```bash
   curl -f https://api.example.com/api/v1/ready
   ```

## 2. Azure PostgreSQL Flexible Server
1. Create server (example):
   ```bash
   az postgres flexible-server create \
     --resource-group <rg> \
     --name <server-name> \
     --location <region> \
     --admin-user <admin-user> \
     --admin-password <strong-password> \
     --sku-name Standard_D2s_v3 \
     --tier GeneralPurpose \
     --version 16 \
     --high-availability ZoneRedundant \
     --storage-size 128
   ```
2. Create DB:
   ```bash
   az postgres flexible-server db create \
     --resource-group <rg> \
     --server-name <server-name> \
     --database-name lms
   ```
3. Allow VM public IP:
   ```bash
   az postgres flexible-server firewall-rule create \
     --resource-group <rg> \
     --name <server-name> \
     --rule-name allow-app-vm \
     --start-ip-address <vm-ip> \
     --end-ip-address <vm-ip>
   ```
4. Configure app connection:
   - `PROD_DATABASE_URL=postgresql+psycopg2://<user>:<password>@<server>.postgres.database.azure.com:5432/lms?sslmode=require`

## 3. GitHub Actions Auto Deploy
Workflow: `.github/workflows/deploy-azure-vm.yml`

Set GitHub `Environment: production` secrets:
- `AZURE_VM_HOST`
- `AZURE_VM_USER`
- `AZURE_VM_SSH_KEY`
- `PROD_DATABASE_URL`
- `SECRET_KEY`
- `APP_DOMAIN`
- `LETSENCRYPT_EMAIL`
- `FRONTEND_BASE_URL`
- `CORS_ORIGINS`
- `TRUSTED_HOSTS`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `SMTP_USE_TLS` (optional, default `true`)
- `SMTP_USE_SSL` (optional, default `false`)
- `SENTRY_DSN` (optional)

On push to `main`, the workflow copies a release archive to the VM and runs `scripts/deploy_azure_vm.sh`.

## 4. SMTP Provider (Recommended: Resend)
Production SMTP values:
- `SMTP_HOST=smtp.resend.com`
- `SMTP_PORT=587`
- `SMTP_USERNAME=resend`
- `SMTP_PASSWORD=<resend_api_key>`
- `SMTP_USE_TLS=true`
- `SMTP_USE_SSL=false`
- `EMAIL_FROM=<verified-sender@your-domain>`

Connection test:
```bash
python scripts/test_smtp_connection.py
python scripts/test_smtp_connection.py --to your-email@example.com
```

Provider notes:
- Supabase does not provide a production relay for your backend app; for Supabase Auth, configure custom SMTP with the same provider credentials.
- Firebase custom SMTP requires Identity Platform; default Firebase Auth email flow is not a direct replacement for backend SMTP settings.
