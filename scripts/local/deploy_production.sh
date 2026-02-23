#!/bin/bash
# Production Deployment Script for LMS Backend

echo "Starting LMS Backend Production Deployment..."

# Step 1: Apply database migrations
echo "Applying database migrations..."
cd "$(dirname "$0")/.."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Database migration failed!"
    exit 1
fi
echo "✅ Database migrations applied successfully"

# Step 2: Build frontend (if needed)
echo "Building frontend..."
cd frontend/educonnect-pro
npm install --production
npm run build
cd ../..

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi
echo "✅ Frontend built successfully"

# Step 3: Deploy Docker containers
echo "Deploying Docker containers..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

if [ $? -ne 0 ]; then
    echo "❌ Docker deployment failed!"
    exit 1
fi
echo "✅ Docker containers deployed successfully"

# Step 4: Verify deployment
echo "Verifying deployment..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/ready)
if [ "$HEALTH_CHECK" = "200" ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed: HTTP $HEALTH_CHECK"
    exit 1
fi

# Step 5: Open Swagger in production (for verification)
echo "Opening Swagger UI in production..."
echo "Swagger UI available at: https://egylms.duckdns.org/docs"
echo "Note: API docs are disabled in production by default (ENABLE_API_DOCS=false)"
echo "To enable temporarily for verification, set ENABLE_API_DOCS=true in .env.production"

echo "🎉 Production deployment completed successfully!"
echo "Please verify the new instructor and admin endpoints:"
echo "- POST /api/v1/instructors/register"
echo "- POST /api/v1/admin/setup"
echo "- GET /api/v1/instructors/onboarding-status"
echo "- GET /api/v1/admin/onboarding-status"

# Optional: Enable API docs temporarily for verification
# echo "Enabling API docs temporarily for verification..."
# sed -i 's/ENABLE_API_DOCS=false/ENABLE_API_DOCS=true/' .env.production
# docker-compose -f docker-compose.prod.yml restart app