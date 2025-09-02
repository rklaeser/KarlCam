#!/bin/bash
# Deploy v2 collector job to Cloud Run Jobs
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
COLLECTOR_IMAGE_TAG="${COLLECTOR_IMAGE_TAG:-v2}"
BUCKET_NAME="${BUCKET_NAME:-karlcam-v2-data}"

echo "📝 Deploying KarlCam V2 Collector Job"
echo "====================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${COLLECTOR_IMAGE_TAG}"
echo "  • Bucket: ${BUCKET_NAME}"

# Set project
gcloud config set project ${PROJECT_ID}

# Get Cloud SQL connection details (shared instance)
DB_INSTANCE_NAME="karlcam-db"
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Cloud SQL instance not found. Run init-v2.sh first."
    exit 1
fi

# Build and push collector image using production Dockerfile
echo "📦 Building v2 collector image..."
cd "${PROJECT_ROOT}"
docker build --platform linux/amd64 -f collect/infra/Dockerfile.prod -t gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG} .

echo "⬆️  Pushing v2 collector image..."
docker push gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG}

# Initialize database if needed
echo "🗃️  Setting up v2 database initialization job..."
if ! gcloud run jobs describe karlcam-db-init-v2 --region ${REGION} --quiet 2>/dev/null; then
    echo "Creating v2 database initialization job..."
    gcloud run jobs create karlcam-db-init-v2 \
      --image gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG} \
      --region ${REGION} \
      --memory 512Mi \
      --cpu 1 \
      --max-retries 2 \
      --parallelism 1 \
      --set-cloudsql-instances ${CONNECTION_NAME} \
      --set-secrets "DATABASE_URL=database-url-v2:latest" \
      --command python \
      --args db/init_db.py
    
    echo "Running v2 database initialization..."
    gcloud run jobs execute karlcam-db-init-v2 --region ${REGION} --wait
else
    echo "V2 database initialization job already exists"
    echo "To reinitialize, run: gcloud run jobs execute karlcam-db-init-v2 --region ${REGION}"
fi

# Deploy v2 data collection job
echo "📝 Deploying v2 data collection job..."
if gcloud run jobs describe karlcam-collector-v2 --region ${REGION} --quiet 2>/dev/null; then
    echo "Updating existing v2 data collection job..."
    gcloud run jobs update karlcam-collector-v2 \
      --image gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG} \
      --region ${REGION}
else
    echo "Creating v2 data collection job..."
    gcloud run jobs create karlcam-collector-v2 \
      --image gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG} \
      --region ${REGION} \
      --memory 2Gi \
      --cpu 1 \
      --max-retries 1 \
      --parallelism 1 \
      --set-cloudsql-instances ${CONNECTION_NAME} \
      --set-env-vars "USE_CLOUD_STORAGE=true,OUTPUT_BUCKET=${BUCKET_NAME}" \
      --set-secrets "DATABASE_URL=database-url-v2:latest,GEMINI_API_KEY=gemini-api-key-v2:latest" \
      --args="-m,collect.collect_images"
fi

echo ""
echo "✅ V2 Collector Job Deployed!"
echo "============================="
echo "  • Job Name: karlcam-collector-v2"
echo "  • Run manually: gcloud run jobs execute karlcam-collector-v2 --region=${REGION}"
echo "  • View logs: gcloud run jobs logs read karlcam-collector-v2 --region=${REGION}"
echo ""
echo "📅 Next Steps:"
echo "  1. Set up automatic v2 collection:"
echo "     ./setup-scheduler-v2.sh"
echo ""
echo "  2. Manual v2 collection commands:"
echo "     gcloud run jobs execute karlcam-collector-v2 --region=${REGION}  # Run once"
echo "     gcloud scheduler jobs run karlcam-collector-v2-schedule --location=${REGION}  # Test scheduler"
echo ""
echo "  3. Monitor v2 collection:"
echo "     gcloud scheduler jobs list --location=${REGION}  # View scheduled jobs"
echo "     gcloud run jobs logs read karlcam-collector-v2 --region=${REGION}  # View logs"