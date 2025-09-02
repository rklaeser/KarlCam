#!/bin/bash
# Setup infrastructure for KarlCam (Cloud SQL, Storage, Secrets)
set -e

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    source .env
    echo "✅ Loaded environment variables from .env"
else
    echo "⚠️  No .env file found. Make sure GEMINI_API_KEY is set."
    exit 1
fi

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
BUCKET_NAME="${BUCKET_NAME:-karlcam-fog-data}"

echo "🔧 Setting up KarlCam Infrastructure"
echo "===================================="

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

# Create Cloud Storage bucket
echo "📦 Creating Cloud Storage bucket..."
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET_NAME} 2>/dev/null || echo "Bucket already exists"

# Setup Cloud SQL
echo "🗄️  Setting up Cloud SQL instance..."
DB_INSTANCE_NAME="karlcam-db"
DB_NAME="karlcam"
DB_USER="karlcam"

# Use database password from environment or generate new one
if [ -n "${DATABASE_PASSWORD}" ]; then
    echo "Using DATABASE_PASSWORD from environment"
    DB_PASSWORD="${DATABASE_PASSWORD}"
else
    echo "Generating new database password"
    DB_PASSWORD=$(openssl rand -base64 20)
fi

# Create Cloud SQL instance (if it doesn't exist)
if ! gcloud sql instances describe ${DB_INSTANCE_NAME} --quiet 2>/dev/null; then
    echo "Creating new Cloud SQL instance..."
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
    echo "Cloud SQL instance already exists"
fi

# Create database
echo "📋 Creating database..."
gcloud sql databases create ${DB_NAME} --instance=${DB_INSTANCE_NAME} 2>/dev/null || echo "Database already exists"

# Reset and create user
echo "👤 Setting up database user..."
gcloud sql users delete ${DB_USER} --instance=${DB_INSTANCE_NAME} --quiet 2>/dev/null || echo "User didn't exist"
gcloud sql users create ${DB_USER} --instance=${DB_INSTANCE_NAME} --password=${DB_PASSWORD}

# Get connection name for Cloud SQL
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)')
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/karlcam?host=/cloudsql/${CONNECTION_NAME}"

echo "✅ Cloud SQL setup complete!"
echo "   Instance: ${DB_INSTANCE_NAME}"
echo "   Connection: ${CONNECTION_NAME}"

# Setup secrets in Secret Manager
echo "🔐 Setting up secrets in Secret Manager..."

# Store GEMINI_API_KEY
if ! gcloud secrets describe gemini-api-key --quiet 2>/dev/null; then
    echo -n "${GEMINI_API_KEY}" | gcloud secrets create gemini-api-key --data-file=-
else
    echo -n "${GEMINI_API_KEY}" | gcloud secrets versions add gemini-api-key --data-file=-
fi

# Store DATABASE_URL
if ! gcloud secrets describe database-url --quiet 2>/dev/null; then
    echo -n "${DATABASE_URL}" | gcloud secrets create database-url --data-file=-
else
    echo -n "${DATABASE_URL}" | gcloud secrets versions add database-url --data-file=-
fi

# Grant Secret Manager access to compute service account
echo "🔐 Setting up IAM permissions..."
COMPUTE_SA=$(gcloud iam service-accounts list --filter="displayName:Compute Engine default service account" --format="value(email)")
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo ""
echo "✅ Infrastructure Setup Complete!"
echo "================================="
echo "  • Cloud Storage: gs://${BUCKET_NAME}"
echo "  • Cloud SQL: ${DB_INSTANCE_NAME}"
echo "  • Database: ${DB_NAME}"
echo "  • Secrets: gemini-api-key, database-url"
echo ""
echo "📝 Next Steps:"
echo "  1. Deploy collector: ../collect/infra/deploy.sh"
echo "  2. Deploy API: ../web/api/infra/deploy.sh"
echo "  3. Deploy admin backend: ../admin/backend/infra/deploy.sh"
echo "  4. Deploy frontend: ../web/frontend/infra/deploy.sh"
echo "  5. Deploy admin frontend: ../admin/frontend/infra/deploy.sh"
echo "  6. Or deploy all: ./deploy.sh"