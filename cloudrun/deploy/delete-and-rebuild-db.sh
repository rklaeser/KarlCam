#!/bin/bash
# Delete and rebuild KarlCam Cloud SQL database with fresh schema
# Modeled after the original deploy.sh database setup

set -e

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    source .env
    echo "✅ Loaded environment variables from .env"
else
    echo "⚠️  No .env file found. Make sure DATABASE_PASSWORD is set if you want to reuse existing password."
fi

PROJECT_ID="karlcam"
REGION="us-central1"
DB_INSTANCE_NAME="karlcam-db"
DB_NAME="karlcam"
DB_USER="karlcam"
COLLECTOR_IMAGE_TAG="v3.0.1"

echo "🗄️  Rebuilding KarlCam Database"
echo "================================"

# Set project
gcloud config set project ${PROJECT_ID}

# Step 0: Enable required APIs (same as deploy.sh)
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com

echo "⏳ Waiting for APIs to be fully enabled..."
sleep 10

# Step 1: Check if Cloud SQL instance exists, create if needed
echo "🔍 Checking Cloud SQL instance..."
if ! gcloud sql instances describe ${DB_INSTANCE_NAME} --quiet 2>/dev/null; then
    echo "Cloud SQL instance doesn't exist. Creating new instance..."
    gcloud sql instances create ${DB_INSTANCE_NAME} \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=${REGION} \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --backup \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=04 \
        --deletion-protection
    
    echo "⏳ Waiting for instance to be ready..."
    sleep 30
else
    echo "✅ Cloud SQL instance exists"
fi

# Step 2: Delete existing database (but keep instance)
echo "🗑️  Deleting existing database..."
gcloud sql databases delete ${DB_NAME} --instance=${DB_INSTANCE_NAME} --quiet 2>/dev/null || echo "Database didn't exist"

# Step 3: Delete and recreate database user to ensure clean state
echo "🔄 Resetting database user..."
gcloud sql users delete ${DB_USER} --instance=${DB_INSTANCE_NAME} --quiet 2>/dev/null || echo "User didn't exist"

# Use database password from environment or generate new one
if [ -n "${DATABASE_PASSWORD}" ]; then
    echo "Using DATABASE_PASSWORD from environment"
    DB_PASSWORD="${DATABASE_PASSWORD}"
else
    echo "Generating new database password"
    DB_PASSWORD=$(openssl rand -base64 20)
fi

# Step 4: Recreate database and user
echo "📋 Creating fresh database and user..."
gcloud sql databases create ${DB_NAME} --instance=${DB_INSTANCE_NAME}
gcloud sql users create ${DB_USER} --instance=${DB_INSTANCE_NAME} --password=${DB_PASSWORD}

# Get connection name for Cloud SQL
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)')
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/karlcam?host=/cloudsql/${CONNECTION_NAME}"

echo "✅ Database recreated!"
echo "   Instance: ${DB_INSTANCE_NAME}"
echo "   Database: ${DB_NAME}"
echo "   User: ${DB_USER}"
echo "   Connection: ${CONNECTION_NAME}"

# Step 5: Update DATABASE_URL secret in Secret Manager
echo "🔐 Updating DATABASE_URL secret..."
echo -n "${DATABASE_URL}" | gcloud secrets versions add database-url --data-file=-
echo "✅ Secret updated!"

# Step 6: Delete existing database initialization job (to ensure fresh run)
echo "🗑️  Removing existing database init job..."
gcloud run jobs delete karlcam-db-init --region ${REGION} --quiet 2>/dev/null || echo "Job didn't exist"

# Step 7: Create fresh database initialization job
echo "🔨 Creating database initialization job..."
gcloud run jobs create karlcam-db-init \
  --image gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG} \
  --region ${REGION} \
  --memory 512Mi \
  --cpu 1 \
  --max-retries 2 \
  --parallelism 1 \
  --set-cloudsql-instances ${CONNECTION_NAME} \
  --set-secrets "DATABASE_URL=database-url:latest" \
  --command python \
  --args collect/init_db.py

# Step 8: Run database initialization to create schema and load data
echo "🚀 Initializing database schema and loading webcam data..."
gcloud run jobs execute karlcam-db-init --region ${REGION} --wait

echo ""
echo "✅ Database Rebuild Complete!"
echo "============================="
echo ""
echo "📋 What was done:"
echo "  • Deleted old database: ${DB_NAME}"
echo "  • Recreated fresh database and user"
echo "  • Updated DATABASE_URL secret"
echo "  • Ran schema initialization (schema.sql)"
echo "  • Loaded webcam data from webcams.json"
echo ""
echo "🔗 Database Details:"
echo "  • Instance: ${DB_INSTANCE_NAME}"
echo "  • Database: ${DB_NAME}" 
echo "  • Connection: ${CONNECTION_NAME}"
echo ""
echo "📝 Next Steps:"
echo "  1. Test collector: gcloud run jobs execute karlcam-collector --region=${REGION}"
echo "  2. Check logs: gcloud run logs read karlcam-db-init --region=${REGION}"
echo "  3. Verify data: Connect to Cloud SQL and check tables"
echo ""
echo "⚠️  Database Password:"
if [ -n "${DATABASE_PASSWORD}" ]; then
    echo "  Used existing DATABASE_PASSWORD from environment"
else
    echo "  Generated new password: ${DB_PASSWORD}"
    echo "  💡 Save this password if you need direct database access"
fi
echo ""