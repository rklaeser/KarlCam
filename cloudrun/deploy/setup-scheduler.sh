#!/bin/bash
# Set up Cloud Scheduler to run KarlCam data collection every 10 minutes

set -e

PROJECT_ID="karlcam"
REGION="us-central1"

echo "⏰ Setting up Cloud Scheduler for KarlCam"
echo "========================================"

# Set project
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling App Engine and Cloud Scheduler APIs..."
gcloud services enable appengine.googleapis.com
gcloud services enable cloudscheduler.googleapis.com

# Create App Engine app if it doesn't exist (required for Cloud Scheduler)
if ! gcloud app describe --project=${PROJECT_ID} --quiet 2>/dev/null; then
    echo "📱 Creating App Engine app (required for Cloud Scheduler)..."
    gcloud app create --region=us-central --project=${PROJECT_ID}
else
    echo "App Engine app already exists"
fi

echo "⏳ Waiting for App Engine to be ready..."
sleep 10

# Create Cloud Scheduler job (idempotent)
if gcloud scheduler jobs describe karlcam-collector-schedule --location=${REGION} --quiet 2>/dev/null; then
    echo "Scheduler job already exists, skipping creation..."
else
    echo "Creating scheduler job..."
    gcloud scheduler jobs create http karlcam-collector-schedule \
        --location=${REGION} \
        --schedule="*/10 * * * *" \
        --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/karlcam-collector:run" \
        --http-method=POST \
        --oauth-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com" \
        --headers="Content-Type=application/json" \
        --message-body='{}' \
        --description="Run KarlCam data collection every 10 minutes"
fi

echo ""
echo "✅ Cloud Scheduler Setup Complete!"
echo "=================================="
echo ""
echo "📅 Schedule: Every 10 minutes"
echo "🎯 Target: karlcam-collector Cloud Run Job"
echo ""
echo "📝 Next Steps:"
echo "  1. Monitor: gcloud scheduler jobs list --location=${REGION}"
echo "  2. Test run: gcloud scheduler jobs run karlcam-collector-schedule --location=${REGION}"
echo "  3. View logs: gcloud run jobs logs read karlcam-collector --region=${REGION}"
echo ""
echo "⚠️  To disable automatic collection:"
echo "  gcloud scheduler jobs pause karlcam-collector-schedule --location=${REGION}"
echo ""