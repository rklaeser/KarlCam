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
cd /Users/reed/Code/Homelab/KarlCam/infra
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
- **Admin Backend:** Complete rewrite - removed dual scoring, added filtering (cameras, time, confidence, fog levels)
- **Admin Frontend:** Complete rewrite - modern gallery view with sidebar filters, infinite scroll, modal details

### ⚠️ Current Issues:
- **Gemini API Limits:** Hit daily quota, collector paused via `gcloud scheduler jobs pause karlcam-collector-schedule`
- **Deployments Needed:** Recent code changes not yet deployed to Cloud Run

### 🔄 Component-Based Deployments:

**Each component now has its own deployment infrastructure in `{component}/infra/`:**

1. **Collector:** 
   ```bash
   cd ../../collect/infra
   ./deploy.sh
   ```

2. **API Service:**
   ```bash
   cd ../../web/api/infra
   ./deploy.sh
   ```

3. **Admin Backend:**
   ```bash
   cd ../../admin/backend/infra
   ./deploy.sh
   ```

4. **Admin Frontend:**
   ```bash
   cd ../../admin/frontend/infra
   ./deploy.sh
   ```

5. **Main Frontend:**
   ```bash
   cd ../../web/frontend/infra
   ./deploy.sh
   ```

**Or deploy everything at once:**
```bash
cd /path/to/KarlCam/infra
./deploy.sh all
```

### 📅 Tomorrow:
1. **Resume Collector:** `gcloud scheduler jobs resume karlcam-collector-schedule --location=us-central1`
2. **Deploy Updated Services:** Run the deployment commands above
3. **Test New Admin Interface:** Verify filtering, pagination, and image browsing works
4. **Monitor Gemini Usage:** Check if API limits reset and collection resumes properly

### 🏗️ Architecture Changes:
- **Component-Based Deployment:** Each component has its own `infra/` directory with `.dev` and `.prod` Dockerfiles
- **Centralized Database:** All components use shared `db/` module with proper data models
- **Separated Collect/Label:** Collection and labeling are independent stages with multiple labeler support
- **Admin System:** Transformed from approval workflow to browsing interface
- **Clean Infrastructure:** `infra/` only contains infrastructure and orchestration scripts