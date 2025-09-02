#!/bin/bash
# Deploy remaining tables migration job to Cloud Run Jobs
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
MIGRATION_IMAGE_TAG="${MIGRATION_IMAGE_TAG:-remaining-migrate}"

echo "🔄 Deploying KarlCam Images & Labels Migration Job"
echo "=============================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${MIGRATION_IMAGE_TAG}"

# Set project
gcloud config set project ${PROJECT_ID}

# Get Cloud SQL connection details
DB_INSTANCE_NAME="karlcam-db"
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Cloud SQL instance not found."
    exit 1
fi

# Build and push migration image using collector Dockerfile (has all dependencies)
echo "📦 Building migration job image..."
cd "${PROJECT_ROOT}"
docker build --platform linux/amd64 -f collect/infra/Dockerfile.prod -t gcr.io/${PROJECT_ID}/karlcam-migrate:${MIGRATION_IMAGE_TAG} .

echo "⬆️  Pushing migration job image..."
docker push gcr.io/${PROJECT_ID}/karlcam-migrate:${MIGRATION_IMAGE_TAG}

# Deploy remaining tables migration job
echo "🔄 Deploying remaining tables migration job..."
if gcloud run jobs describe karlcam-migrate-remaining --region ${REGION} --quiet 2>/dev/null; then
    echo "Updating existing remaining tables migration job..."
    gcloud run jobs update karlcam-migrate-remaining \
      --image gcr.io/${PROJECT_ID}/karlcam-migrate:${MIGRATION_IMAGE_TAG} \
      --region ${REGION}
else
    echo "Creating remaining tables migration job..."
    gcloud run jobs create karlcam-migrate-remaining \
      --image gcr.io/${PROJECT_ID}/karlcam-migrate:${MIGRATION_IMAGE_TAG} \
      --region ${REGION} \
      --memory 1Gi \
      --cpu 1 \
      --max-retries 1 \
      --parallelism 1 \
      --set-cloudsql-instances ${CONNECTION_NAME} \
      --set-secrets "DATABASE_URL=database-url:latest,DATABASE_URL_V2=database-url-v2:latest" \
      --command python \
      --args db/migrate_remaining_tables.py
fi

echo ""
echo "✅ Remaining Tables Migration Job Deployed!"
echo "=========================================="
echo "  • Job Name: karlcam-migrate-remaining"
echo "  • Run migration: gcloud run jobs execute karlcam-migrate-remaining --region=${REGION}"
echo "  • View logs: gcloud run jobs logs read karlcam-migrate-remaining --region=${REGION}"