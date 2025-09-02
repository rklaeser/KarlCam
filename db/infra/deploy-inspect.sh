#!/bin/bash
# Deploy schema inspection job to Cloud Run Jobs
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
JOB_IMAGE_TAG="${JOB_IMAGE_TAG:-latest}"

echo "🔍 Deploying Schema Inspection Job"
echo "=================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${JOB_IMAGE_TAG}"

# Set project
gcloud config set project ${PROJECT_ID}

# Get Cloud SQL connection details
DB_INSTANCE_NAME="karlcam-db"
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Cloud SQL instance not found. Run init.sh first."
    exit 1
fi

# Build and push job image (reuse collector image)
echo "📦 Building inspection job image..."
cd "${PROJECT_ROOT}"
docker build --platform linux/amd64 -f collect/infra/Dockerfile.prod -t gcr.io/${PROJECT_ID}/karlcam-db-tools:${JOB_IMAGE_TAG} .

echo "⬆️  Pushing inspection job image..."
docker push gcr.io/${PROJECT_ID}/karlcam-db-tools:${JOB_IMAGE_TAG}

# Deploy schema inspection job
echo "🔍 Deploying schema inspection job..."
if gcloud run jobs describe karlcam-schema-inspect --region ${REGION} --quiet 2>/dev/null; then
    echo "Updating existing schema inspection job..."
    gcloud run jobs update karlcam-schema-inspect \
      --image gcr.io/${PROJECT_ID}/karlcam-db-tools:${JOB_IMAGE_TAG} \
      --region ${REGION}
else
    echo "Creating schema inspection job..."
    gcloud run jobs create karlcam-schema-inspect \
      --image gcr.io/${PROJECT_ID}/karlcam-db-tools:${JOB_IMAGE_TAG} \
      --region ${REGION} \
      --memory 512Mi \
      --cpu 1 \
      --max-retries 2 \
      --parallelism 1 \
      --set-cloudsql-instances ${CONNECTION_NAME} \
      --set-secrets "DATABASE_URL=database-url:latest" \
      --args="-m,db.inspect_schema"
fi

echo ""
echo "✅ Schema Inspection Job Deployed!"
echo "=================================="
echo "  • Run inspection: gcloud run jobs execute karlcam-schema-inspect --region=${REGION}"
echo "  • View logs: gcloud run logs read karlcam-schema-inspect --region=${REGION}"