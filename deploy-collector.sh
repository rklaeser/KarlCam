#!/bin/bash
# Quick deployment script for the dual scoring collector
# Use this to deploy just the collector to start collecting data

set -e

PROJECT_ID="karlcam"
REGION="us-central1"
BUCKET_NAME="karlcam-fog-data"

echo "🚀 Deploying KarlCam Dual Scoring Collector"
echo "============================================"

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Set project
gcloud config set project ${PROJECT_ID}

# Step 1: Create Cloud Storage bucket
echo "📦 Creating Cloud Storage bucket..."
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET_NAME} 2>/dev/null || echo "Bucket already exists"

# Step 2: Build and push collector image  
echo "🔨 Building collector image..."
docker build --platform linux/amd64 -f gke/docker/Dockerfile.collector -t gcr.io/${PROJECT_ID}/karlcam-collector:v3.0.0 .

echo "📤 Pushing image to Container Registry..."
gcloud auth configure-docker
docker push gcr.io/${PROJECT_ID}/karlcam-collector:v3.0.0

# Step 3: Create namespace and secrets
echo "☸️  Setting up Kubernetes resources..."
kubectl create namespace karlcam --dry-run=client -o yaml | kubectl apply -f -

# Create secret for Gemini API key (you'll need to update this)
echo "🔑 Creating secret for Gemini API key..."
echo "⚠️  IMPORTANT: You need to set your Gemini API key!"
echo "   Run this command with your actual key:"
echo "   kubectl create secret generic karlcam-secrets --from-literal=GEMINI_API_KEY='your-key-here' -n karlcam --dry-run=client -o yaml | kubectl apply -f -"

# Create a placeholder secret for now
kubectl create secret generic karlcam-secrets --from-literal=GEMINI_API_KEY='PLACEHOLDER-SET-YOUR-KEY' -n karlcam --dry-run=client -o yaml | kubectl apply -f -

# Step 4: Deploy CronJob
echo "📅 Deploying collector CronJob..."
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: karlcam-labeling
  namespace: karlcam
  labels:
    app: karlcam-labeling
    component: data-collection
spec:
  schedule: "*/10 * * * *"  # Every 10 minutes
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            app: karlcam-labeling
            component: data-collection
        spec:
          restartPolicy: OnFailure
          containers:
          - name: labeling
            image: gcr.io/${PROJECT_ID}/karlcam-collector:v3.0.0
            command: ["python", "-m", "collect.collect_and_label"]
            
            resources:
              requests:
                cpu: "0.5"
                memory: "1Gi"
              limits:
                cpu: "1"
                memory: "2Gi"
            
            env:
            - name: PYTHONPATH
              value: "/app"
            - name: USE_CLOUD_STORAGE
              value: "true"
            - name: OUTPUT_BUCKET
              value: "${BUCKET_NAME}"
            - name: GEMINI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: karlcam-secrets
                  key: GEMINI_API_KEY
EOF

# Step 5: Verify deployment
echo "✅ Deployment complete!"
echo ""
echo "🔍 Verifying deployment..."
kubectl get cronjob karlcam-labeling -n karlcam

echo ""
echo "✅ KarlCam Dual Scoring Collector Deployed!"
echo "============================================"
echo ""
echo "📊 What's happening:"
echo "  • Collector runs every 10 minutes"
echo "  • Uses both Gemini Vision API + Computer Vision heuristics"
echo "  • Saves data to: gs://${BUCKET_NAME}"
echo "  • Flags disagreements for manual review"
echo ""
echo "🔑 NEXT STEP - Set your Gemini API key:"
echo "   kubectl create secret generic karlcam-secrets \\"
echo "     --from-literal=GEMINI_API_KEY='your-actual-key' \\"
echo "     -n karlcam --dry-run=client -o yaml | kubectl apply -f -"
echo ""
echo "📊 Monitor the collector:"
echo "   kubectl get pods -n karlcam"
echo "   kubectl logs -f job/[job-name] -n karlcam"
echo ""
echo "☁️  View collected data:"
echo "   gsutil ls gs://${BUCKET_NAME}/"
echo "   gsutil cat gs://${BUCKET_NAME}/latest_collection_summary.json"
echo ""
echo "💰 Cost: ~$10-20/month (CronJob + Storage + Gemini API calls)"