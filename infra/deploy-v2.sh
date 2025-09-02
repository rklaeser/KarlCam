#!/bin/bash
# Main v2 deployment orchestrator for KarlCam with karl.cam domain
# Calls individual v2 deployment scripts for each component
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Configuration (can be overridden by environment variables)
export PROJECT_ID="${PROJECT_ID:-karlcam}"
export REGION="${REGION:-us-central1}"
export BUCKET_NAME="${BUCKET_NAME:-karlcam-v2-data}"

# Use v2 tags for all images
export COLLECTOR_IMAGE_TAG="${COLLECTOR_IMAGE_TAG:-v2}"
export API_IMAGE_TAG="${API_IMAGE_TAG:-v2}"
export FRONTEND_IMAGE_TAG="${FRONTEND_IMAGE_TAG:-v2}"
export ADMIN_BACKEND_IMAGE_TAG="${ADMIN_BACKEND_IMAGE_TAG:-v2}"
export ADMIN_FRONTEND_IMAGE_TAG="${ADMIN_FRONTEND_IMAGE_TAG:-v2}"

echo "🚀 Deploying KarlCam V2 - Full Serverless Architecture"
echo "======================================================"
echo ""
echo "Configuration:"
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Bucket: ${BUCKET_NAME}"
echo "  • Domain: karl.cam"
echo "  • Image Tags: v2"
echo ""

# Check if individual scripts exist
if [ ! -f "${SCRIPT_DIR}/init-v2.sh" ]; then
    echo "❌ Missing init-v2.sh in ${SCRIPT_DIR}"
    exit 1
fi

# Parse command line arguments
if [ "$#" -gt 0 ]; then
    case "$1" in
        infrastructure|infra)
            echo "🔧 Deploying v2 infrastructure only..."
            "${SCRIPT_DIR}/init-v2.sh"
            ;;
        collector)
            echo "📝 Deploying v2 collector only..."
            "${SCRIPT_DIR}/../collect/infra/deploy-v2.sh"
            ;;
        api)
            echo "🚀 Deploying v2 API only..."
            "${SCRIPT_DIR}/../web/api/infra/deploy-v2.sh"
            ;;
        frontend)
            echo "🌐 Deploying v2 frontend only..."
            "${SCRIPT_DIR}/../web/frontend/infra/deploy-v2.sh"
            ;;
        admin-backend)
            echo "🔍 Deploying v2 admin backend only..."
            "${SCRIPT_DIR}/../admin/backend/infra/deploy-v2.sh"
            ;;
        admin-frontend)
            echo "🎨 Deploying v2 admin frontend only..."
            "${SCRIPT_DIR}/../admin/frontend/infra/deploy-v2.sh"
            ;;
        admin)
            echo "📊 Deploying v2 admin system (backend + frontend)..."
            "${SCRIPT_DIR}/../admin/backend/infra/deploy-v2.sh"
            echo ""
            "${SCRIPT_DIR}/../admin/frontend/infra/deploy-v2.sh"
            ;;
        all|"")
            # Deploy everything in order
            echo "🔧 Step 1/5: Setting up v2 infrastructure..."
            echo "==========================================="
            "${SCRIPT_DIR}/init-v2.sh"
            echo ""
            
            echo "📝 Step 2/5: Deploying v2 collector job..."
            echo "=========================================="
            "${SCRIPT_DIR}/../collect/infra/deploy-v2.sh"
            echo ""
            
            echo "🚀 Step 3/5: Deploying v2 API service..."
            echo "========================================"
            "${SCRIPT_DIR}/../web/api/infra/deploy-v2.sh"
            echo ""
            
            echo "🌐 Step 4/5: Deploying v2 frontend..."
            echo "====================================="
            "${SCRIPT_DIR}/../web/frontend/infra/deploy-v2.sh"
            echo ""
            
            echo "📊 Step 5/5: Deploying v2 admin system..."
            echo "========================================"
            "${SCRIPT_DIR}/../admin/backend/infra/deploy-v2.sh"
            echo ""
            "${SCRIPT_DIR}/../admin/frontend/infra/deploy-v2.sh"
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
    "${SCRIPT_DIR}/deploy-v2.sh" all
fi

if [ "$1" == "all" ] || [ "$#" -eq 0 ]; then
    echo ""
    echo "✅ Full KarlCam V2 Deployment Complete!"
    echo "======================================="
    echo ""
    echo "📊 V2 Architecture:"
    echo "  • Data Collection: Cloud Run Job (karlcam-collector-v2)"
    echo "  • API: https://api.karl.cam"
    echo "  • Frontend: https://karl.cam"
    echo "  • Admin: https://admin.karl.cam"
    echo "  • Database: Cloud SQL PostgreSQL (karlcam-db)"
    echo "  • Storage: Cloud Storage (${BUCKET_NAME})"
    echo ""
    echo "💰 Cost Model:"
    echo "  • Serverless: Pay only for what you use"
    echo "  • Estimated: ~$5-15/month"
    echo ""
    echo "📝 Quick Commands:"
    echo "  • Test API: curl https://api.karl.cam/api/public/cameras"
    echo "  • Run collector: gcloud run jobs execute karlcam-collector-v2 --region=${REGION}"
    echo "  • View logs: gcloud run logs read [service-name-v2] --region=${REGION}"
    echo "  • Schedule collection: ../collect/infra/setup-scheduler-v2.sh"
    echo ""
    echo "🔄 Individual V2 Deployments:"
    echo "  • ./deploy-v2.sh api             # Update API only"
    echo "  • ./deploy-v2.sh frontend        # Update frontend only"
    echo "  • ./deploy-v2.sh collector       # Update collector only"
    echo "  • ./deploy-v2.sh admin           # Deploy admin system"
    echo "  • ./deploy-v2.sh admin-backend   # Update admin backend only"
    echo "  • ./deploy-v2.sh admin-frontend  # Update admin frontend only"
fi