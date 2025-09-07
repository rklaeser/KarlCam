#!/bin/bash
# Setup Cloud Build triggers for KarlCam staging and production deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
REPO_NAME="KarlCam"
REPO_OWNER="Klaeser-Homelab"  # Updated to match actual GitHub connection

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check prerequisites
log "Checking prerequisites..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI is not installed. Please install it first."
fi

# Set project
gcloud config set project ${PROJECT_ID}

# Check if GitHub app is connected
log "Checking GitHub connection..."
GITHUB_CONNECTION=$(gcloud builds connections list --region=${REGION} --format="value(name)" 2>/dev/null | head -n1)

if [ -z "$GITHUB_CONNECTION" ]; then
    warn "No GitHub connection found. You need to connect your GitHub repository first."
    echo ""
    echo "Please follow these steps:"
    echo "1. Go to https://console.cloud.google.com/cloud-build/triggers;region=${REGION}?project=${PROJECT_ID}"
    echo "2. Click 'Connect Repository'"
    echo "3. Select 'GitHub' and authenticate"
    echo "4. Select repository: ${REPO_OWNER}/${REPO_NAME}"
    echo "5. Then run this script again"
    echo ""
    read -p "Press Enter after completing the GitHub connection setup..."
    
    # Check again
    GITHUB_CONNECTION=$(gcloud builds connections list --region=${REGION} --format="value(name)" 2>/dev/null | head -n1)
    if [ -z "$GITHUB_CONNECTION" ]; then
        error "GitHub connection still not found. Please complete the setup and try again."
    fi
fi

log "GitHub connection found: ${GITHUB_CONNECTION}"

# Get the repository ID
REPO_ID=$(gcloud builds repositories list --connection="${GITHUB_CONNECTION}" --region=${REGION} --format="value(name)" 2>/dev/null | grep -i "${REPO_NAME}" | head -n1)

if [ -z "$REPO_ID" ]; then
    warn "Repository not found. Creating repository link..."
    gcloud builds repositories create ${REPO_NAME} \
        --remote-uri="https://github.com/${REPO_OWNER}/${REPO_NAME}.git" \
        --connection="${GITHUB_CONNECTION}" \
        --region="${REGION}"
    
    REPO_ID=$(gcloud builds repositories list --connection="${GITHUB_CONNECTION}" --region=${REGION} --format="value(name)" 2>/dev/null | grep -i "${REPO_NAME}" | head -n1)
fi

log "Repository ID: ${REPO_ID}"

# Create Terraform state bucket if it doesn't exist
log "Setting up Terraform state bucket..."
TERRAFORM_BUCKET="karlcam-terraform-state"
if ! gsutil ls -b gs://${TERRAFORM_BUCKET} &>/dev/null; then
    log "Creating Terraform state bucket..."
    gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${TERRAFORM_BUCKET}
    gsutil versioning set on gs://${TERRAFORM_BUCKET}
else
    log "Terraform state bucket already exists"
fi

# Create secrets if they don't exist
log "Setting up secrets in Secret Manager..."

# Database password
if ! gcloud secrets describe database-password --project=${PROJECT_ID} &>/dev/null; then
    warn "Secret 'database-password' not found."
    echo "Please enter the database password:"
    read -s DB_PASSWORD
    echo -n "${DB_PASSWORD}" | gcloud secrets create database-password --data-file=- --project=${PROJECT_ID}
    log "Created secret: database-password"
else
    log "Secret 'database-password' already exists"
fi

# Gemini API key
if ! gcloud secrets describe gemini-api-key --project=${PROJECT_ID} &>/dev/null; then
    warn "Secret 'gemini-api-key' not found."
    echo "Please enter the Gemini API key:"
    read -s GEMINI_KEY
    echo -n "${GEMINI_KEY}" | gcloud secrets create gemini-api-key --data-file=- --project=${PROJECT_ID}
    log "Created secret: gemini-api-key"
else
    log "Secret 'gemini-api-key' already exists"
fi

# Grant Cloud Build access to secrets
log "Granting Cloud Build access to secrets..."
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud secrets add-iam-policy-binding database-password \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --project=${PROJECT_ID} &>/dev/null

gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --project=${PROJECT_ID} &>/dev/null

log "Secrets configured successfully"

# Delete existing triggers if they exist
log "Checking for existing triggers..."
EXISTING_TRIGGERS=$(gcloud builds triggers list --region=${REGION} --format="value(name)" 2>/dev/null)

if echo "$EXISTING_TRIGGERS" | grep -q "karlcam-staging"; then
    log "Deleting existing staging trigger..."
    gcloud builds triggers delete karlcam-staging --region=${REGION} --quiet
fi

if echo "$EXISTING_TRIGGERS" | grep -q "karlcam-production"; then
    log "Deleting existing production trigger..."
    gcloud builds triggers delete karlcam-production --region=${REGION} --quiet
fi

# Create staging trigger (auto-deploy)
log "Creating staging trigger (auto-deploy)..."
gcloud builds triggers create github \
    --repo-name="${REPO_ID}" \
    --branch-pattern="^staging$" \
    --build-config="cloudbuild.yaml" \
    --name="karlcam-staging" \
    --description="Auto-deploy to staging environment" \
    --region="${REGION}" \
    --substitutions="_PROJECT_ID=${PROJECT_ID},_REGION=${REGION},_DATABASE_PASSWORD=\$(SECRET:database-password),_GEMINI_API_KEY=\$(SECRET:gemini-api-key)" \
    --include-logs-with-status

log "✅ Staging trigger created successfully"

# Create production trigger (requires approval)
log "Creating production trigger (requires manual approval)..."
gcloud builds triggers create github \
    --repo-name="${REPO_ID}" \
    --branch-pattern="^main$" \
    --build-config="cloudbuild.yaml" \
    --name="karlcam-production" \
    --description="Deploy to production (requires approval)" \
    --region="${REGION}" \
    --require-approval \
    --substitutions="_PROJECT_ID=${PROJECT_ID},_REGION=${REGION},_DATABASE_PASSWORD=\$(SECRET:database-password),_GEMINI_API_KEY=\$(SECRET:gemini-api-key)" \
    --include-logs-with-status

log "✅ Production trigger created successfully"

# Summary
echo ""
log "🎉 Cloud Build triggers setup completed!"
echo ""
echo "📋 Trigger Configuration:"
echo "  • Staging Trigger: karlcam-staging"
echo "    - Branch: staging"
echo "    - Auto-deploy: YES"
echo "    - Environment: staging.karl.cam"
echo ""
echo "  • Production Trigger: karlcam-production"
echo "    - Branch: main"
echo "    - Auto-deploy: NO (requires manual approval)"
echo "    - Environment: karl.cam"
echo ""
echo "📊 How it works:"
echo "  1. Push to 'staging' branch → Automatic deployment to staging"
echo "  2. Push to 'main' branch → Requires manual approval in Cloud Console"
echo ""
echo "🔗 Cloud Build Console:"
echo "  https://console.cloud.google.com/cloud-build/triggers;region=${REGION}?project=${PROJECT_ID}"
echo ""
echo "📝 Next steps:"
echo "  1. Create a 'staging' branch if it doesn't exist:"
echo "     git checkout -b staging"
echo "     git push origin staging"
echo ""
echo "  2. Test staging deployment:"
echo "     git push origin staging"
echo ""
echo "  3. For production deployment:"
echo "     git checkout main"
echo "     git merge staging"
echo "     git push origin main"
echo "     Then approve in Cloud Console"
echo ""
echo "✅ Setup complete!"