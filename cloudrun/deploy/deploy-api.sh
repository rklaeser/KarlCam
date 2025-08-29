#!/bin/bash
# Deploy API service to Cloud Run
set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
API_IMAGE_TAG="${API_IMAGE_TAG:-latest}"
BUCKET_NAME="${BUCKET_NAME:-karlcam-fog-data}"

echo "🚀 Deploying KarlCam API Service"
echo "================================="

# Set project
gcloud config set project ${PROJECT_ID}

# Get Cloud SQL connection details
DB_INSTANCE_NAME="karlcam-db"
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Cloud SQL instance not found. Run deploy-infrastructure.sh first."
    exit 1
fi

# Build and push API image
echo "📦 Building API image..."
cd /Users/reed/Code/Homelab/KarlCam
docker build --platform linux/amd64 -f api/Dockerfile -t gcr.io/${PROJECT_ID}/karlcam-api:${API_IMAGE_TAG} .

echo "⬆️  Pushing API image..."
docker push gcr.io/${PROJECT_ID}/karlcam-api:${API_IMAGE_TAG}

# Deploy API service
echo "☁️  Deploying API service to Cloud Run..."
gcloud run deploy karlcam-api \
  --image gcr.io/${PROJECT_ID}/karlcam-api:${API_IMAGE_TAG} \
  --region ${REGION} \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 100 \
  --port 8000 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "BUCKET_NAME=${BUCKET_NAME}" \
  --add-cloudsql-instances ${CONNECTION_NAME} \
  --set-secrets "DATABASE_URL=database-url:latest"

echo ""
echo "✅ API Service Deployed!"
echo "========================"
echo "  • URL: https://api.karlcam.xyz"
echo "  • Test: curl https://api.karlcam.xyz/api/public/cameras"
echo "  • Logs: gcloud run logs read karlcam-api --region=${REGION}"