# Production Deployment Guide for LMS Backend

This guide provides step-by-step instructions for deploying the enhanced instructor and admin account creation flows to production at `https://egylms.duckdns.org`.

## 📋 Prerequisites

### Required Access
- **Azure Portal access** (for Azure deployments)
- **Docker access** on production server
- **SSH access** to production server
- **Database administrator access**

### Environment Setup
- Production database (Azure PostgreSQL Flexible Server)
- Redis instance for rate limiting
- Caddy reverse proxy configured
- SSL certificates for `egylms.duckdns.org`

## 🚀 Deployment Steps

### Step 1: Prepare Database Migrations
```bash
# Generate and verify migrations
cd K:\business\projects\lms_backend
alembic revision --autogenerate -m "Add instructors and admins tables"
```

### Step 2: Update Production Configuration
1. Update `.env.production` with actual secrets (replace REDACTED placeholders)
2. Ensure `ENABLE_API_DOCS=false` for security in production
3. Verify CORS origins include `https://egylms.duckdns.org`

### Step 3: Deploy to Production

#### Option A: Using Deployment Script (Recommended)
```bash
# Windows
scripts\deploy_production.bat

# Linux/Mac
chmod +x scripts/deploy_production.sh
scripts/deploy_production.sh
```

#### Option B: Manual Deployment
1. **Apply database migrations:**
   ```bash
   alembic upgrade head
   ```

2. **Build frontend:**
   ```bash
   cd frontend/educonnect-pro
   npm install --production
   npm run build
   ```

3. **Deploy Docker containers:**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Step 4: Verify Production Deployment

#### Health Checks
- `GET https://egylms.duckdns.org/api/v1/ready` → Should return `200 OK`
- `GET https://egylms.duckdns.org/metrics` → Should return Prometheus metrics
- `GET https://egylms.duckdns.org/docs` → Should show Swagger UI (if enabled)

#### Test New Endpoints
```bash
# Test instructor registration endpoint
curl -X POST https://egylms.duckdns.org/api/v1/instructors/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-instructor@example.com",
    "password": "TestPassword123!",
    "full_name": "Test Instructor",
    "role": "instructor",
    "bio": "Test bio for instructor",
    "expertise": ["Test"],
    "teaching_experience_years": 1,
    "education_level": "Test",
    "institution": "Test University"
  }'

# Test admin setup endpoint  
curl -X POST https://egylms.duckdns.org/api/v1/admin/setup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email": "test-admin@example.com",
    "password": "VeryStrongPassword123456!",
    "full_name": "Test Admin",
    "role": "admin",
    "security_level": "enhanced",
    "mfa_required": true,
    "security_policy_accepted": true,
    "security_policy_version": "1.0"
  }'
```

## 🔐 Security Verification

### Critical Security Checks
1. ✅ **HttpOnly cookies** are set for auth endpoints
2. ✅ **CSP policy** includes new endpoints
3. ✅ **Rate limiting** is applied to new endpoints
4. ✅ **Input validation** prevents XSS in instructor bio fields
5. ✅ **MFA enforcement** for admin accounts

### Swagger in Production
The Swagger UI is available at:
- **Production**: `https://egylms.duckdns.org/docs`
- **Note**: API documentation is disabled by default in production (`ENABLE_API_DOCS=false`)
- To temporarily enable for verification, set `ENABLE_API_DOCS=true` in `.env.production` and restart the app

## 🔄 Rollback Procedure

### Immediate Rollback
1. **Database rollback:**
   ```bash
   alembic downgrade -1
   ```

2. **Docker rollback:**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   # Restore previous Docker image
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Frontend rollback:**
   ```bash
   # Serve previous static build
   cp backup/dist/* /var/www/html/
   ```

## 📊 Post-Deployment Monitoring

### Key Metrics to Monitor
- **Error rates**: Sentry error tracking
- **Response times**: Prometheus/Grafana
- **Authentication success/failure**: Log analysis
- **New user registration rates**: Analytics dashboard

### Alert Configuration
- Set up alerts for:
  - 500 errors on instructor/admin endpoints
  - Authentication failures > 10/min
  - Database connection issues
  - High response times (> 2s)

## ✅ Deployment Checklist

- [ ] Database migrations applied successfully
- [ ] Frontend built and deployed
- [ ] Docker containers running
- [ ] Health check passes
- [ ] Instructor registration endpoint working
- [ ] Admin setup endpoint working
- [ ] Security features verified
- [ ] Monitoring and alerts configured
- [ ] Rollback procedure tested

## 📝 Additional Notes

- **Maintenance window**: Schedule during low-traffic hours
- **Communication**: Notify stakeholders before deployment
- **Testing**: Conduct UAT in staging before production
- **Documentation**: Update runbooks with new procedures

This guide ensures safe and reliable deployment of the enhanced instructor and admin account creation flows to production.