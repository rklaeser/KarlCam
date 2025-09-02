#!/bin/bash
# Deploy collector job to Cloud Run Jobs
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
COLLECTOR_IMAGE_TAG="${COLLECTOR_IMAGE_TAG:-latest}"
BUCKET_NAME="${BUCKET_NAME:-karlcam-fog-data}"

echo "📝 Deploying KarlCam Collector Job"
echo "==================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${COLLECTOR_IMAGE_TAG}"
echo "  • Bucket: ${BUCKET_NAME}"

# Set project
gcloud config set project ${PROJECT_ID}

# Get Cloud SQL connection details
DB_INSTANCE_NAME="karlcam-db"
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Cloud SQL instance not found. Run init.sh first."
    exit 1
fi

# Build and push collector image using production Dockerfile
echo "📦 Building collector image..."
cd "${PROJECT_ROOT}"
docker build --platform linux/amd64 -f collect/infra/Dockerfile.prod -t gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG} .

echo "⬆️  Pushing collector image..."
docker push gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG}

# Initialize database if needed
echo "🗃️  Setting up database initialization job..."
if ! gcloud run jobs describe karlcam-db-init --region ${REGION} --quiet 2>/dev/null; then
    echo "Creating database initialization job..."
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
      --args db/init_db.py
    
    echo "Running database initialization..."
    gcloud run jobs execute karlcam-db-init --region ${REGION} --wait
else
    echo "Database initialization job already exists"
    echo "To reinitialize, run: gcloud run jobs execute karlcam-db-init --region ${REGION}"
fi

# Deploy data collection job
echo "📝 Deploying data collection job..."
if gcloud run jobs describe karlcam-collector --region ${REGION} --quiet 2>/dev/null; then
    echo "Updating existing data collection job..."
    gcloud run jobs update karlcam-collector \
      --image gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG} \
      --region ${REGION}
else
    echo "Creating data collection job..."
    gcloud run jobs create karlcam-collector \
      --image gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG} \
      --region ${REGION} \
      --memory 2Gi \
      --cpu 1 \
      --max-retries 1 \
      --parallelism 1 \
      --set-cloudsql-instances ${CONNECTION_NAME} \
      --set-env-vars "USE_CLOUD_STORAGE=true,OUTPUT_BUCKET=${BUCKET_NAME}" \
      --set-secrets "DATABASE_URL=database-url:latest,GEMINI_API_KEY=gemini-api-key:latest" \
      --args="-m,collect.collect_images"
fi

echo ""
echo "✅ Collector Job Deployed!"
echo "=========================="
echo "  • Job Name: karlcam-collector"
echo "  • Run manually: gcloud run jobs execute karlcam-collector --region=${REGION}"
echo "  • View logs: gcloud run logs read karlcam-collector --region=${REGION}"
echo ""
echo "📅 Next Steps:"
echo "  1. Set up automatic collection:"
echo "     ./setup-scheduler.sh"
echo ""
echo "  2. Manual collection commands:"
echo "     gcloud run jobs execute karlcam-collector --region=${REGION}  # Run once"
echo "     gcloud scheduler jobs run karlcam-collector-schedule --location=${REGION}  # Test scheduler"
echo ""
echo "  3. Monitor collection:"
echo "     gcloud scheduler jobs list --location=${REGION}  # View scheduled jobs"
echo "     gcloud run logs read karlcam-collector --region=${REGION}  # View logs"