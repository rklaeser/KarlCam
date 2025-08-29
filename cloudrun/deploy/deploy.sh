#!/bin/bash
# Deploy fully serverless KarlCam architecture on Cloud Run
# Replaces GKE with Cloud Run Jobs and Services

set -e

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    source .env
    echo "✅ Loaded environment variables from .env"
else
    echo "⚠️  No .env file found. Make sure GEMINI_API_KEY is set."
    exit 1
fi

PROJECT_ID="karlcam"
REGION="us-central1"
BUCKET_NAME="karlcam-fog-data"
COLLECTOR_IMAGE_TAG="v3.0.1"
API_IMAGE_TAG="v2.0.1"
FRONTEND_IMAGE_TAG="v2.0.3"

echo "🚀 Deploying Fully Serverless KarlCam Architecture"
echo "=================================================="

# Set project
gcloud config set project ${PROJECT_ID}

# Step 0: Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable sqladmin.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com

echo "⏳ Waiting for APIs to be fully enabled..."
sleep 10

# Step 1: Create Cloud Storage bucket for fog data
echo "📦 Creating Cloud Storage bucket..."
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET_NAME} 2>/dev/null || echo "Bucket already exists"

# Step 2: Create Cloud SQL instance for structured data
echo "🗄️  Creating Cloud SQL instance..."
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


# Delete and recreate database user to ensure clean state
echo "Resetting database user..."
gcloud sql users delete ${DB_USER} --instance=${DB_INSTANCE_NAME} --quiet 2>/dev/null || echo "User didn't exist"

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

# Create database and user
echo "📋 Setting up database and user..."
gcloud sql databases create ${DB_NAME} --instance=${DB_INSTANCE_NAME} 2>/dev/null || echo "Database already exists"
gcloud sql users create ${DB_USER} --instance=${DB_INSTANCE_NAME} --password=${DB_PASSWORD} 2>/dev/null || echo "User may already exist"

# Get connection name for Cloud SQL
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)')
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/karlcam?host=/cloudsql/${CONNECTION_NAME}"

echo "✅ Cloud SQL setup complete!"
echo "   Instance: ${DB_INSTANCE_NAME}"
echo "   Connection: ${CONNECTION_NAME}"

# Step 3: Store secrets in Secret Manager
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

echo "✅ Secrets configured!"

# Grant Secret Manager access to compute service account
echo "🔐 Setting up IAM permissions for Cloud Run..."
COMPUTE_SA=$(gcloud iam service-accounts list --filter="displayName:Compute Engine default service account" --format="value(email)")
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${COMPUTE_SA}" --role="roles/secretmanager.secretAccessor" --quiet

# Step 4: Build and push images
echo "🔨 Building and pushing images..."
cd /Users/reed/Code/Homelab/KarlCam

# Build collector image
echo "📦 Building collector image..."
docker build --platform linux/amd64 -f cloudrun/docker/Dockerfile.collector -t gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG} .
docker push gcr.io/${PROJECT_ID}/karlcam-collector:${COLLECTOR_IMAGE_TAG}

# Build API image
echo "📦 Building API image..."
docker build --platform linux/amd64 -f api/Dockerfile -t gcr.io/${PROJECT_ID}/karlcam-api:${API_IMAGE_TAG} .
docker push gcr.io/${PROJECT_ID}/karlcam-api:${API_IMAGE_TAG}

# Step 5: Initialize database schema
echo "🗃️  Initializing database schema..."

# Create or update database initialization job (idempotent)
if gcloud run jobs describe karlcam-db-init --region ${REGION} --quiet 2>/dev/null; then
    echo "Database init job already exists, skipping creation..."
else
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
      --args collect/init_db.py
fi

# Run database initialization only if tables don't exist
echo "🚀 Checking if database initialization is needed..."
if gcloud sql databases describe karlcam --instance=karlcam-db --quiet 2>/dev/null; then
    echo "Database already exists, skipping initialization..."
else
    echo "Running database initialization..."
    gcloud run jobs execute karlcam-db-init --region ${REGION} --wait
fi

# Step 6: Deploy data collection job
echo "📝 Deploying data collection job..."

# Create data collection job (idempotent)
if gcloud run jobs describe karlcam-collector --region ${REGION} --quiet 2>/dev/null; then
    echo "Data collection job already exists, skipping creation..."
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
      --args="-m,collect.collect_and_label"
fi

# Step 7: Note about scheduler setup
echo "⏰ Scheduler setup moved to separate script..."
echo "   Run './setup-scheduler.sh' to enable automatic data collection"

# Step 8: Deploy API (if not already deployed)
echo "☁️  Deploying/updating API service..."

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

# Get API URL
API_URL=$(gcloud run services describe karlcam-api --region ${REGION} --format 'value(status.url)')

# Step 9: Deploy frontend
echo "🌐 Building and deploying frontend..."

# Build frontend with API URL
docker build --platform linux/amd64 \
  --build-arg REACT_APP_API_URL=${API_URL} \
  -f frontend/Dockerfile \
  -t gcr.io/${PROJECT_ID}/karlcam-frontend:${FRONTEND_IMAGE_TAG} .

docker push gcr.io/${PROJECT_ID}/karlcam-frontend:${FRONTEND_IMAGE_TAG}

gcloud run deploy karlcam-frontend \
  --image gcr.io/${PROJECT_ID}/karlcam-frontend:${FRONTEND_IMAGE_TAG} \
  --region ${REGION} \
  --memory 256Mi \
  --cpu 1 \
  --timeout 30 \
  --concurrency 100 \
  --port 80 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 5

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe karlcam-frontend --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Fully Serverless Deployment Complete!"
echo "========================================"
echo ""
echo "📊 New Architecture:"
echo "  • Data Collection: Cloud Run Job triggered by Cloud Scheduler (every 10 min)"
echo "  • Scoring Methods: Gemini Vision API + Computer Vision Heuristics"  
echo "  • Structured Data: Cloud SQL PostgreSQL (${DB_INSTANCE_NAME})"
echo "  • Image Storage: Cloud Storage bucket (${BUCKET_NAME})"
echo "  • API: Cloud Run Service (serverless)"
echo "  • Frontend: Cloud Run Service (serverless)"
echo ""
echo "🔗 URLs:"
echo "  • API: ${API_URL}"
echo "  • Frontend: ${FRONTEND_URL}"
echo ""
echo "💰 Cost Savings:"
echo "  Before: ~$100/month (GKE cluster + backend)"
echo "  After: ~$5-15/month (pay per use)"
echo "  Savings: ~$85-95/month!"
echo ""
echo "📝 Next Steps:"
echo "  1. Test API: curl ${API_URL}/api/public/cameras"
echo "  2. Access frontend: open ${FRONTEND_URL}"
echo "  3. Set up custom domain: ./setup-domain.sh (for karlcam.xyz)"
echo "  4. Enable auto collection: ./setup-scheduler.sh"
echo "  5. Monitor logs: gcloud run logs read karlcam-collector --region=${REGION}"
echo ""
echo "⚠️  To clean up old GKE resources, run:"
echo "  kubectl delete namespace karlcam"
echo ""