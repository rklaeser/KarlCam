#!/bin/bash
# Setup v2 infrastructure for KarlCam (Cloud SQL, Storage, Secrets) with karl.cam domain
set -e

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    source .env
    echo "✅ Loaded environment variables from .env"
else
    echo "⚠️  No .env file found. Make sure GEMINI_API_KEY is set."
    exit 1
fi

# Configuration - V2 with new naming
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
BUCKET_NAME="${BUCKET_NAME:-karlcam-v2-data}"

echo "🔧 Setting up KarlCam V2 Infrastructure"
echo "======================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}" 
echo "  • Bucket: ${BUCKET_NAME}"
echo "  • Domain: karl.cam"

# Set project
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable sqladmin.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com

echo "⏳ Waiting for APIs to be fully enabled..."
sleep 10

# Create Cloud Storage bucket for v2
echo "📦 Creating Cloud Storage bucket for v2..."
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET_NAME} 2>/dev/null || echo "Bucket already exists"

# Setup Cloud SQL v2 - use existing instance, create new database
echo "🗄️  Setting up Cloud SQL v2 database..."
DB_INSTANCE_NAME="karlcam-db"  # Use existing instance
DB_NAME="karlcam_v2"
DB_USER="karlcam_v2"

# Use database password from environment or generate new one
if [ -n "${DATABASE_PASSWORD}" ]; then
    echo "Using DATABASE_PASSWORD from environment"
    DB_PASSWORD="${DATABASE_PASSWORD}"
else
    echo "Generating new database password for v2"
    DB_PASSWORD=$(openssl rand -base64 20)
fi

# Verify existing Cloud SQL instance exists
if ! gcloud sql instances describe ${DB_INSTANCE_NAME} --quiet 2>/dev/null; then
    echo "❌ Cloud SQL instance ${DB_INSTANCE_NAME} not found. Run init.sh first to create the base instance."
    exit 1
else
    echo "✅ Using existing Cloud SQL instance: ${DB_INSTANCE_NAME}"
fi

# Create v2 database
echo "📋 Creating v2 database..."
gcloud sql databases create ${DB_NAME} --instance=${DB_INSTANCE_NAME} 2>/dev/null || echo "Database already exists"

# Create v2 user
echo "👤 Setting up v2 database user..."
gcloud sql users delete ${DB_USER} --instance=${DB_INSTANCE_NAME} --quiet 2>/dev/null || echo "User didn't exist"
gcloud sql users create ${DB_USER} --instance=${DB_INSTANCE_NAME} --password=${DB_PASSWORD}

# Get connection name for Cloud SQL
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)')
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"

echo "✅ Cloud SQL v2 database setup complete!"
echo "   Instance: ${DB_INSTANCE_NAME} (shared)"
echo "   Database: ${DB_NAME}" 
echo "   User: ${DB_USER}"
echo "   Connection: ${CONNECTION_NAME}"

# Setup secrets in Secret Manager for v2
echo "🔐 Setting up v2 secrets in Secret Manager..."

# Store GEMINI_API_KEY (reuse existing or create v2 version)
if ! gcloud secrets describe gemini-api-key-v2 --quiet 2>/dev/null; then
    echo -n "${GEMINI_API_KEY}" | gcloud secrets create gemini-api-key-v2 --data-file=-
else
    echo -n "${GEMINI_API_KEY}" | gcloud secrets versions add gemini-api-key-v2 --data-file=-
fi

# Store DATABASE_URL for v2
if ! gcloud secrets describe database-url-v2 --quiet 2>/dev/null; then
    echo -n "${DATABASE_URL}" | gcloud secrets create database-url-v2 --data-file=-
else
    echo -n "${DATABASE_URL}" | gcloud secrets versions add database-url-v2 --data-file=-
fi

# Grant Secret Manager access to compute service account
echo "🔐 Setting up IAM permissions for v2..."
COMPUTE_SA=$(gcloud iam service-accounts list --filter="displayName:Compute Engine default service account" --format="value(email)")
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo ""
echo "✅ KarlCam V2 Infrastructure Setup Complete!"
echo "============================================"
echo "  • Cloud Storage: gs://${BUCKET_NAME}"
echo "  • Cloud SQL: ${DB_INSTANCE_NAME}"
echo "  • Database: ${DB_NAME}"
echo "  • Secrets: gemini-api-key-v2, database-url-v2"
echo "  • Domain: karl.cam"
echo ""
echo "📝 Next Steps:"
echo "  1. Deploy collector v2: ../collect/infra/deploy-v2.sh"
echo "  2. Deploy API v2: ../web/api/infra/deploy-v2.sh"
echo "  3. Deploy admin backend v2: ../admin/backend/infra/deploy-v2.sh"
echo "  4. Deploy frontend v2: ../web/frontend/infra/deploy-v2.sh"
echo "  5. Deploy admin frontend v2: ../admin/frontend/infra/deploy-v2.sh"
echo "  6. Or deploy all v2: ./deploy-v2.sh"