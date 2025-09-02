#!/bin/bash
# Main deployment orchestrator for KarlCam
# Calls individual deployment scripts for each component
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Configuration (can be overridden by environment variables)
export PROJECT_ID="${PROJECT_ID:-karlcam}"
export REGION="${REGION:-us-central1}"
export BUCKET_NAME="${BUCKET_NAME:-karlcam-fog-data}"

# Use latest tags by default for all images
export COLLECTOR_IMAGE_TAG="${COLLECTOR_IMAGE_TAG:-latest}"
export API_IMAGE_TAG="${API_IMAGE_TAG:-latest}"
export FRONTEND_IMAGE_TAG="${FRONTEND_IMAGE_TAG:-latest}"

echo "🚀 Deploying Fully Serverless KarlCam Architecture"
echo "=================================================="
echo ""
echo "Configuration:"
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Bucket: ${BUCKET_NAME}"
echo "  • Image Tags: latest"
echo ""

# Check if individual scripts exist
if [ ! -f "${SCRIPT_DIR}/init.sh" ]; then
    echo "❌ Missing init.sh in ${SCRIPT_DIR}"
    exit 1
fi

# Parse command line arguments
if [ "$#" -gt 0 ]; then
    case "$1" in
        infrastructure|infra)
            echo "🔧 Deploying infrastructure only..."
            "${SCRIPT_DIR}/init.sh"
            ;;
        collector)
            echo "📝 Deploying collector only..."
            "${SCRIPT_DIR}/../collect/infra/deploy.sh"
            ;;
        api)
            echo "🚀 Deploying API only..."
            "${SCRIPT_DIR}/../web/api/infra/deploy.sh"
            ;;
        frontend)
            echo "🌐 Deploying frontend only..."
            "${SCRIPT_DIR}/../web/frontend/infra/deploy.sh"
            ;;
        admin-backend)
            echo "🔍 Deploying admin backend only..."
            "${SCRIPT_DIR}/../admin/backend/infra/deploy.sh"
            ;;
        admin-frontend)
            echo "🎨 Deploying admin frontend only..."
            "${SCRIPT_DIR}/../admin/frontend/infra/deploy.sh"
            ;;
        admin)
            echo "📊 Deploying admin system (backend + frontend)..."
            "${SCRIPT_DIR}/../admin/backend/infra/deploy.sh"
            echo ""
            "${SCRIPT_DIR}/../admin/frontend/infra/deploy.sh"
            ;;
        all|"")
            # Deploy everything in order
            echo "🔧 Step 1/4: Setting up infrastructure..."
            echo "========================================="
            "${SCRIPT_DIR}/init.sh"
            echo ""
            
            echo "📝 Step 2/4: Deploying collector job..."
            echo "========================================"
            "${SCRIPT_DIR}/../collect/infra/deploy.sh"
            echo ""
            
            echo "🚀 Step 3/4: Deploying API service..."
            echo "======================================"
            "${SCRIPT_DIR}/../web/api/infra/deploy.sh"
            echo ""
            
            echo "🌐 Step 4/4: Deploying frontend..."
            echo "==================================="
            "${SCRIPT_DIR}/../web/frontend/infra/deploy.sh"
            echo ""
            ;;
        *)
            echo "Usage: $0 [infrastructure|collector|api|frontend|admin|admin-backend|admin-frontend|all]"
            echo ""
            echo "Core Components:"
            echo "  infrastructure   - Cloud SQL, Storage, and Secrets setup"
            echo "  collector       - Data collection job"
            echo "  api            - API service"
            echo "  frontend       - Frontend service"
            echo ""
            echo "Admin System:"
            echo "  admin          - Deploy both admin backend and frontend"
            echo "  admin-backend  - Admin backend API only"
            echo "  admin-frontend - Admin frontend UI only"
            echo ""
            echo "  all            - Deploy everything (default)"
            echo ""
            echo "Examples:"
            echo "  $0              # Deploy everything"
            echo "  $0 all          # Deploy everything"
            echo "  $0 api          # Deploy only the API"
            echo "  $0 frontend     # Deploy only the frontend"
            echo "  $0 admin        # Deploy admin system"
            exit 1
            ;;
    esac
else
    # No arguments - deploy everything
    "${SCRIPT_DIR}/deploy.sh" all
fi

if [ "$1" == "all" ] || [ "$#" -eq 0 ]; then
    echo ""
    echo "✅ Full KarlCam Deployment Complete!"
    echo "===================================="
    echo ""
    echo "📊 Architecture:"
    echo "  • Data Collection: Cloud Run Job (karlcam-collector)"
    echo "  • API: https://api.karlcam.xyz"
    echo "  • Frontend: https://karlcam.xyz"
    echo "  • Database: Cloud SQL PostgreSQL"
    echo "  • Storage: Cloud Storage (${BUCKET_NAME})"
    echo ""
    echo "💰 Cost Model:"
    echo "  • Serverless: Pay only for what you use"
    echo "  • Estimated: ~$5-15/month"
    echo ""
    echo "📝 Quick Commands:"
    echo "  • Test API: curl https://api.karlcam.xyz/api/public/cameras"
    echo "  • Run collector: gcloud run jobs execute karlcam-collector --region=${REGION}"
    echo "  • View logs: gcloud run logs read [service-name] --region=${REGION}"
    echo "  • Schedule collection: ../collect/infra/setup-scheduler.sh"
    echo ""
    echo "🔄 Individual Deployments:"
    echo "  • ./deploy.sh api             # Update API only"
    echo "  • ./deploy.sh frontend        # Update frontend only"
    echo "  • ./deploy.sh collector       # Update collector only"
    echo "  • ./deploy.sh review          # Deploy review system"
    echo "  • ./deploy.sh review-backend  # Update review backend only"
    echo "  • ./deploy.sh review-frontend # Update review frontend only"
fi