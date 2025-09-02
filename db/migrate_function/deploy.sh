#!/bin/bash
# Deploy KarlCam migration Cloud Function
set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
FUNCTION_NAME="karlcam-migrate-v2"

echo "🚀 Deploying KarlCam Migration Cloud Function"
echo "============================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}" 
echo "  • Function: ${FUNCTION_NAME}"

# Set project
gcloud config set project ${PROJECT_ID}

# Get Cloud SQL connection details
DB_INSTANCE_NAME="karlcam-db"
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Cloud SQL instance not found."
    exit 1
fi

# Deploy the function
echo "📦 Deploying Cloud Function..."
gcloud functions deploy ${FUNCTION_NAME} \
  --gen2 \
  --runtime python311 \
  --source . \
  --entry-point migrate_karlcam_data \
  --trigger-http \
  --allow-unauthenticated \
  --region ${REGION} \
  --memory 1Gi \
  --timeout 540s

echo ""
echo "✅ Migration Cloud Function Deployed!"
echo "===================================="
echo "  • Function Name: ${FUNCTION_NAME}"
echo "  • URL: https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}"
echo "  • Trigger migration: curl https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}"
echo "  • View logs: gcloud functions logs read ${FUNCTION_NAME} --region=${REGION}"