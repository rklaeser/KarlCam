# KarlCam Deployment Guide

## 🚀 Overview

KarlCam uses a branch-based deployment strategy with Cloud Build and Terraform:
- **staging branch** → Automatic deployment to staging.karl.cam
- **main branch** → Manual approval required for karl.cam production

## 📋 Prerequisites

Before setting up deployments, ensure you have:

1. **Google Cloud Project** with billing enabled
2. **GitHub repository** connected to Cloud Build
3. **Terraform files** in the `terraform/` directory
4. **Secrets configured** in Secret Manager:
   - `database-password`
   - `gemini-api-key`

## 🔧 Initial Setup

### 1. Run the Setup Script

```bash
# Make sure you're in the project root
cd /path/to/KarlCam

# Run the setup script
./scripts/setup-cloud-build-triggers.sh
```

This script will:
- Connect your GitHub repository to Cloud Build
- Create Cloud Build triggers for staging and production
- Set up Terraform state bucket
- Configure secrets access
- Create both triggers with appropriate settings

### 2. Create Staging Branch

If you don't have a staging branch yet:

```bash
git checkout -b staging
git push origin staging
```

## 🎯 Deployment Workflow

### Deploying to Staging (Automatic)

1. **Make changes in your feature branch:**
   ```bash
   git checkout -b feature/new-feature
   # Make your changes
   git add .
   git commit -m "Add new feature"
   ```

2. **Merge to staging:**
   ```bash
   git checkout staging
   git merge feature/new-feature
   git push origin staging
   ```

3. **Automatic deployment happens:**
   - Cloud Build triggers automatically
   - Builds all Docker containers
   - Tags with commit SHA and branch name
   - Deploys to staging environment using Terraform
   - No manual intervention required

4. **Monitor the build:**
   ```bash
   # View build logs
   gcloud builds log --stream $(gcloud builds list --limit=1 --format="value(id)")
   
   # Or view in console:
   # https://console.cloud.google.com/cloud-build/builds
   ```

5. **Verify staging deployment:**
   - Frontend: https://staging.karl.cam
   - API: https://api.staging.karl.cam
   - Admin: https://admin.staging.karl.cam

### Deploying to Production (Manual Approval)

1. **After testing in staging, merge to main:**
   ```bash
   git checkout main
   git merge staging
   git push origin main
   ```

2. **Cloud Build triggers but waits for approval:**
   - Build starts automatically
   - Containers are built and pushed
   - **Deployment pauses for manual approval**

3. **Approve the deployment:**
   - Go to [Cloud Build Console](https://console.cloud.google.com/cloud-build/builds)
   - Find the pending build for the main branch
   - Click on the build
   - Click **"Review"** or **"Approve"**
   - Add optional comment
   - Click **"Approve"** to proceed

4. **Production deployment completes:**
   - Terraform applies production configuration
   - Services are updated with new containers
   - Zero-downtime deployment

5. **Verify production:**
   - Frontend: https://karl.cam
   - API: https://api.karl.cam
   - Admin: https://admin.karl.cam

## 📊 How Cloud Build Works

### The cloudbuild.yaml Flow

1. **Build Phase (Parallel):**
   - All Docker images built simultaneously
   - Frontend builds with environment-specific API URLs
   - Images tagged with SHA, branch name, and 'latest'

2. **Push Phase:**
   - All images pushed to Google Container Registry
   - Multiple tags for easy rollback

3. **Deploy Phase (Conditional):**
   - Only runs for `staging` and `main` branches
   - Uses Terraform with environment-specific configs
   - Staging: Auto-applies changes
   - Production: Requires manual approval first

### Branch Strategy

```
feature/branch
     ↓ (PR & merge)
staging branch → staging.karl.cam (auto-deploy)
     ↓ (test & verify)
main branch → karl.cam (manual approval required)
```

## 🔐 Security & Secrets

### Secrets Management

Secrets are stored in Google Secret Manager and accessed by Cloud Build:

```bash
# View secrets
gcloud secrets list

# Update a secret
echo -n "new-password" | gcloud secrets versions add database-password --data-file=-
```

### Required IAM Permissions

Cloud Build service account needs:
- `roles/secretmanager.secretAccessor`
- `roles/run.admin`
- `roles/storage.admin`
- `roles/cloudsql.admin`

## 🚨 Rollback Procedures

### Quick Rollback to Previous Version

1. **Find the previous good image tag:**
   ```bash
   gcloud container images list-tags gcr.io/karlcam/karlcam-api \
     --limit=10 --format="table(tags,timestamp)"
   ```

2. **Update Terraform with specific tag:**
   ```bash
   cd terraform
   terraform workspace select production
   terraform apply -var="image_tag=PREVIOUS_GOOD_SHA"
   ```

### Emergency Rollback

If Terraform isn't working, directly update Cloud Run:

```bash
# Rollback API service
gcloud run deploy karlcam-api-v2 \
  --image=gcr.io/karlcam/karlcam-api:PREVIOUS_GOOD_SHA \
  --region=us-central1

# Repeat for other services
```

## 📈 Monitoring Deployments

### View Build History

```bash
# List recent builds
gcloud builds list --limit=10

# Get detailed build info
gcloud builds describe BUILD_ID
```

### Check Service Status

```bash
# Check Cloud Run services
gcloud run services list --region=us-central1

# View service logs
gcloud run logs read karlcam-api-v2 --region=us-central1 --limit=50
```

### Terraform State

```bash
# Check current state
cd terraform
terraform workspace select production
terraform show

# See what would change
terraform plan -var-file="environments/production/terraform.tfvars"
```

## 🐛 Troubleshooting

### Build Fails

1. **Check build logs:**
   ```bash
   gcloud builds log --stream BUILD_ID
   ```

2. **Common issues:**
   - Missing secrets: Check Secret Manager
   - Docker build errors: Test locally first
   - Terraform errors: Validate configuration

### Deployment Stuck

1. **Cancel pending approval:**
   - Go to Cloud Build console
   - Find the build
   - Click "Reject" if needed

2. **Force new deployment:**
   ```bash
   git commit --allow-empty -m "Force rebuild"
   git push origin staging  # or main
   ```

### Terraform State Issues

1. **Refresh state:**
   ```bash
   terraform refresh
   ```

2. **Force unlock (if locked):**
   ```bash
   terraform force-unlock LOCK_ID
   ```

## 📚 Additional Resources

- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/best-practices)

## 💡 Tips

1. **Always test in staging first** - Never skip staging
2. **Use meaningful commit messages** - They become your deployment history
3. **Monitor after deployment** - Watch logs for 5-10 minutes
4. **Keep staging close to production** - Same configs, just different scale
5. **Document changes** - Update this guide when process changes

## 🆘 Need Help?

1. Check build logs in Cloud Console
2. Review Terraform plan output
3. Verify secrets are accessible
4. Check IAM permissions
5. Review the cloudbuild.yaml file