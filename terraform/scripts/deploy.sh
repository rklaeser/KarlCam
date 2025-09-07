#!/bin/bash
# KarlCam Terraform Deployment Script
# Handles staging and production deployments with proper workspace management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TERRAFORM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ID="${PROJECT_ID:-karlcam}"

# Functions
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

usage() {
    echo "Usage: $0 <environment> <action> [options]"
    echo ""
    echo "Environments:"
    echo "  staging     - Deploy to staging environment"
    echo "  production  - Deploy to production environment"
    echo ""
    echo "Actions:"
    echo "  plan        - Show what will be deployed"
    echo "  apply       - Deploy the infrastructure"
    echo "  destroy     - Destroy the infrastructure (use with caution!)"
    echo "  init        - Initialize Terraform"
    echo "  validate    - Validate Terraform configuration"
    echo ""
    echo "Options:"
    echo "  --auto-approve    - Skip interactive approval for apply"
    echo "  --image-tag=TAG   - Deploy specific image tag (default: latest)"
    echo "  --var-file=FILE   - Use custom variable file"
    echo ""
    echo "Examples:"
    echo "  $0 staging plan"
    echo "  $0 staging apply --image-tag=v1.2.3"
    echo "  $0 production apply"
    echo "  $0 staging destroy --auto-approve"
    exit 1
}

# Parse arguments
if [ $# -lt 2 ]; then
    usage
fi

ENVIRONMENT=$1
ACTION=$2
shift 2

# Parse options
AUTO_APPROVE=false
IMAGE_TAG="latest"
VAR_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        --image-tag=*)
            IMAGE_TAG="${1#*=}"
            shift
            ;;
        --var-file=*)
            VAR_FILE="${1#*=}"
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
fi

# Validate action
if [[ ! "$ACTION" =~ ^(init|validate|plan|apply|destroy)$ ]]; then
    error "Invalid action: $ACTION. Must be one of: init, validate, plan, apply, destroy"
fi

# Set workspace and var file
WORKSPACE="$ENVIRONMENT"
if [ -z "$VAR_FILE" ]; then
    VAR_FILE="environments/$ENVIRONMENT/terraform.tfvars"
fi

# Check if var file exists
if [ ! -f "$TERRAFORM_DIR/$VAR_FILE" ]; then
    error "Variable file not found: $VAR_FILE"
fi

log "Starting KarlCam deployment"
log "Environment: $ENVIRONMENT"
log "Action: $ACTION"
log "Image Tag: $IMAGE_TAG"
log "Variable File: $VAR_FILE"
log "Workspace: $WORKSPACE"

# Change to terraform directory
cd "$TERRAFORM_DIR"

# Production safety checks
if [ "$ENVIRONMENT" = "production" ] && [ "$ACTION" = "destroy" ]; then
    warn "You are about to DESTROY the PRODUCTION environment!"
    warn "This will delete all data and cannot be undone!"
    if [ "$AUTO_APPROVE" = false ]; then
        read -p "Are you absolutely sure? Type 'destroy production' to continue: " -r
        if [ "$REPLY" != "destroy production" ]; then
            error "Aborted by user"
        fi
    fi
fi

# Initialize Terraform if needed
if [ "$ACTION" = "init" ] || [ ! -d ".terraform" ]; then
    log "Initializing Terraform..."
    terraform init
fi

# Create or select workspace
log "Setting up workspace: $WORKSPACE"
if terraform workspace list | grep -q "$WORKSPACE"; then
    terraform workspace select "$WORKSPACE"
else
    terraform workspace new "$WORKSPACE"
fi

# Validate configuration
if [ "$ACTION" = "validate" ] || [ "$ACTION" != "init" ]; then
    log "Validating Terraform configuration..."
    terraform validate
fi

# Build terraform command with common arguments
TERRAFORM_ARGS=(
    -var-file="$VAR_FILE"
    -var="image_tag=$IMAGE_TAG"
)

# Execute the requested action
case $ACTION in
    plan)
        log "Planning deployment for $ENVIRONMENT..."
        terraform plan "${TERRAFORM_ARGS[@]}"
        ;;
    apply)
        log "Deploying to $ENVIRONMENT..."
        if [ "$AUTO_APPROVE" = true ]; then
            terraform apply -auto-approve "${TERRAFORM_ARGS[@]}"
        else
            terraform apply "${TERRAFORM_ARGS[@]}"
        fi
        
        if [ $? -eq 0 ]; then
            log "Deployment completed successfully!"
            
            # Show useful outputs
            echo ""
            log "Environment URLs:"
            terraform output | grep -E "(service_url|domain)" || true
            
            echo ""
            log "Useful commands:"
            echo "  View logs: gcloud run logs read karlcam-api-v2 --region=us-central1"
            echo "  Run collector: $(terraform output -raw collector_run_command 2>/dev/null || echo 'gcloud run jobs execute karlcam-collector-v2 --region=us-central1')"
        else
            error "Deployment failed!"
        fi
        ;;
    destroy)
        warn "Destroying $ENVIRONMENT environment..."
        if [ "$AUTO_APPROVE" = true ]; then
            terraform destroy -auto-approve "${TERRAFORM_ARGS[@]}"
        else
            terraform destroy "${TERRAFORM_ARGS[@]}"
        fi
        ;;
    *)
        error "Action '$ACTION' not implemented"
        ;;
esac

log "Operation completed: $ACTION on $ENVIRONMENT"