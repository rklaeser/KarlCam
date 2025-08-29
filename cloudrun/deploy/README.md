# KarlCam Cloud Run Deployment

This directory contains the deployment scripts for the fully serverless KarlCam architecture using Cloud Run.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Cloud Scheduler │───▶│  Cloud Run Job  │───▶│   Cloud SQL     │
│  (every 10 min) │    │  (data collect) │    │  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Cloud Storage   │
                       │ (fog images)    │
                       └─────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Users       │───▶│ Cloud Run       │───▶│ Cloud Run API   │
│                 │    │ (frontend)      │    │ (backend)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Cost Comparison

| Component | Before (GKE) | After (Cloud Run) | Savings |
|-----------|--------------|-------------------|---------|
| Cluster | $70/month | $0 | $70/month |
| Backend | $25/month | ~$2-5/month | $20-23/month |
| Frontend | $5/month | ~$1-3/month | $2-4/month |
| **Total** | **~$100/month** | **~$5-15/month** | **~$85-95/month** |

## Prerequisites

1. **Environment file**: Create `.env` with:
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```

2. **Google Cloud CLI**: Authenticated and configured
   ```bash
   gcloud auth login
   gcloud config set project karlcam
   ```

3. **Docker**: For building images

## Deployment

Single command deployment:

```bash
cd /Users/reed/Code/Homelab/KarlCam/cloudrun/deploy
./deploy.sh
```

The script is **idempotent** - you can run it multiple times safely.

## What the script does

1. **Infrastructure Setup**:
   - Enables required Google Cloud APIs
   - Creates Cloud Storage bucket
   - Creates Cloud SQL PostgreSQL instance
   - Sets up Secret Manager secrets

2. **Database Initialization**:
   - Runs schema creation via Cloud Run Job
   - Loads webcam data from `data/webcams.json`

3. **Application Deployment**:
   - Builds and pushes Docker images
   - Deploys data collection as Cloud Run Job
   - Sets up Cloud Scheduler (every 10 minutes)
   - Deploys API as Cloud Run Service
   - Deploys frontend as Cloud Run Service

4. **Configuration**:
   - Links services to Cloud SQL
   - Configures secrets and environment variables
   - Sets up proper IAM permissions

## Monitoring

```bash
# View logs
gcloud run logs read karlcam-collector --region=us-central1
gcloud run logs read karlcam-api --region=us-central1

# Check scheduler
gcloud scheduler jobs list --location=us-central1

# View job executions
gcloud run jobs executions list --region=us-central1 --job=karlcam-collector
```

## Cleanup

To remove everything:

```bash
# Delete Cloud Run services
gcloud run services delete karlcam-api karlcam-frontend --region=us-central1

# Delete Cloud Run jobs
gcloud run jobs delete karlcam-collector karlcam-db-init --region=us-central1

# Delete scheduler
gcloud scheduler jobs delete karlcam-collector-schedule --location=us-central1

# Delete secrets
gcloud secrets delete gemini-api-key database-url karlcam-db-password

# Delete Cloud SQL (careful!)
gcloud sql instances delete karlcam-db
```

## Migration from GKE

After successful deployment, clean up GKE resources:

```bash
kubectl delete namespace karlcam
```

See `OBSOLETE_FILES.md` for files that can be removed after migration.

---

## Current Status & Next Steps

**Date: August 28, 2025**

### ✅ Completed Today:
- **Database:** Rebuilt Cloud SQL with fresh schema using `delete-and-rebuild-db.sh`
- **Collector:** Fixed `database.py` to handle missing columns (removed `avg_confidence` references)
- **Review Backend:** Complete rewrite - removed dual scoring, added filtering (cameras, time, confidence, fog levels)
- **Review Frontend:** Complete rewrite - modern gallery view with sidebar filters, infinite scroll, modal details

### ⚠️ Current Issues:
- **Gemini API Limits:** Hit daily quota, collector paused via `gcloud scheduler jobs pause karlcam-collector-schedule`
- **Deployments Needed:** Recent code changes not yet deployed to Cloud Run

### 🔄 Pending Deployments:
1. **Collector:** 
   ```bash
   # Rebuild and deploy collector with database fixes
   docker build --platform linux/amd64 -f cloudrun/docker/Dockerfile.collector -t gcr.io/karlcam/karlcam-collector:v3.0.2 .
   docker push gcr.io/karlcam/karlcam-collector:v3.0.2
   gcloud run jobs update karlcam-collector --image gcr.io/karlcam/karlcam-collector:v3.0.2 --region us-central1
   ```

2. **Review Backend:**
   ```bash
   # Deploy new review backend with filtering API
   docker build --platform linux/amd64 -f cloudrun/docker/Dockerfile.review-backend -t gcr.io/karlcam/karlcam-review-backend:v2.0.0 .
   docker push gcr.io/karlcam/karlcam-review-backend:v2.0.0
   gcloud run deploy karlcam-review-backend --image gcr.io/karlcam/karlcam-review-backend:v2.0.0 --region us-central1
   ```

3. **Review Frontend:**
   ```bash
   # Deploy new gallery-style review frontend  
   docker build --platform linux/amd64 -f cloudrun/docker/Dockerfile.review-frontend -t gcr.io/karlcam/karlcam-review-frontend:v2.0.0 .
   docker push gcr.io/karlcam/karlcam-review-frontend:v2.0.0
   gcloud run deploy karlcam-review-frontend --image gcr.io/karlcam/karlcam-review-frontend:v2.0.0 --region us-central1
   ```

### 📅 Tomorrow:
1. **Resume Collector:** `gcloud scheduler jobs resume karlcam-collector-schedule --location=us-central1`
2. **Deploy Updated Services:** Run the deployment commands above
3. **Test New Review Interface:** Verify filtering, pagination, and image browsing works
4. **Monitor Gemini Usage:** Check if API limits reset and collection resumes properly

### 🏗️ Architecture Changes:
- **Review System:** Transformed from approval workflow to browsing interface
- **Database:** Single source of truth, no more file-based storage
- **Frontend:** Modern gallery with filtering instead of one-by-one review