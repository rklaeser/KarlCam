#!/bin/bash
# Deploy old database inspection job to Cloud Run Jobs
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
INSPECTION_IMAGE_TAG="${INSPECTION_IMAGE_TAG:-inspect-old-db}"

echo "🔍 Deploying Old Database Inspection Job"
echo "======================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${INSPECTION_IMAGE_TAG}"

# Set project
gcloud config set project ${PROJECT_ID}

# Get Cloud SQL connection details
DB_INSTANCE_NAME="karlcam-db"
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Cloud SQL instance not found."
    exit 1
fi

# Build and push inspection image
echo "📦 Building inspection job image..."
cd "${PROJECT_ROOT}"
docker build --platform linux/amd64 -f collect/infra/Dockerfile.prod -t gcr.io/${PROJECT_ID}/karlcam-migrate:${INSPECTION_IMAGE_TAG} .

echo "⬆️  Pushing inspection job image..."
docker push gcr.io/${PROJECT_ID}/karlcam-migrate:${INSPECTION_IMAGE_TAG}

# Deploy inspection job
echo "🔄 Deploying old database inspection job..."
if gcloud run jobs describe karlcam-inspect-old-db --region ${REGION} --quiet 2>/dev/null; then
    echo "Updating existing inspection job..."
    gcloud run jobs update karlcam-inspect-old-db \
      --image gcr.io/${PROJECT_ID}/karlcam-migrate:${INSPECTION_IMAGE_TAG} \
      --region ${REGION}
else
    echo "Creating inspection job..."
    gcloud run jobs create karlcam-inspect-old-db \
      --image gcr.io/${PROJECT_ID}/karlcam-migrate:${INSPECTION_IMAGE_TAG} \
      --region ${REGION} \
      --memory 1Gi \
      --cpu 1 \
      --max-retries 1 \
      --parallelism 1 \
      --set-cloudsql-instances ${CONNECTION_NAME} \
      --set-secrets "DATABASE_URL=database-url:latest" \
      --command python \
      --args db/inspect_old_db.py
fi

echo ""
echo "✅ Old Database Inspection Job Deployed!"
echo "======================================="
echo "  • Job Name: karlcam-inspect-old-db"
echo "  • Run inspection: gcloud run jobs execute karlcam-inspect-old-db --region=${REGION}"
echo "  • View logs: gcloud run jobs logs read karlcam-inspect-old-db --region=${REGION}"