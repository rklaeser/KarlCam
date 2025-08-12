#!/bin/bash
# Build and Deploy KarlCam to K8s cluster
# This script builds the images locally first, then transfers them to the remote Docker host

set -e

# Configuration
DOCKER_HOST="${DOCKER_HOST:-tcp://10.0.0.35:2375}"
K8S_HOST="${K8S_HOST:-10.0.0.40}"
NAMESPACE="karlcam"

echo "=== KarlCam Build and Deploy ==="
echo "Docker Host: $DOCKER_HOST"
echo "K8s Host: $K8S_HOST"
echo ""

# Step 1: Build images locally using docker-compose
echo "Step 1: Building Docker images locally..."
docker compose -f docker-compose.prod.yml build

# Step 2: Tag images with the correct naming pattern
echo "Step 2: Tagging images with correct names..."
docker tag karlcam-pipeline:latest karlcam-pipeline:latest 2>/dev/null || true
docker tag karlcam-backend:latest karlcam-backend:latest 2>/dev/null || true
docker tag karlcam-public-frontend:latest karlcam-public-frontend:latest 2>/dev/null || true
docker tag karlcam-pipeline-frontend:latest karlcam-pipeline-frontend:latest 2>/dev/null || true

# Check if images were built with compose service names
docker tag fogcam-pipeline:latest karlcam-pipeline:latest 2>/dev/null || true
docker tag karlcam-backend:latest karlcam-backend:latest 2>/dev/null || true
docker tag karlcam-public-frontend:latest karlcam-public-frontend:latest 2>/dev/null || true
docker tag fogcam-pipeline-frontend:latest karlcam-pipeline-frontend:latest 2>/dev/null || true

# List images to verify
echo "Available images:"
docker images | grep karlcam || echo "No karlcam images found yet"
docker images | grep fogcam || echo "No fogcam images found yet"

# Step 3: Set up Docker context for remote host
echo "Step 3: Setting up Docker context..."
docker context create k8s-deploy --docker host=$DOCKER_HOST 2>/dev/null || true

# Step 4: Transfer images to remote Docker host
echo "Step 4: Transferring images to remote Docker host..."
for service in pipeline backend public-frontend pipeline-frontend; do
    image_name="karlcam-${service}:latest"
    echo "Transferring $image_name to remote Docker..."
    
    # First check if the image exists locally
    if docker image inspect "$image_name" >/dev/null 2>&1; then
        docker save "$image_name" | docker --context k8s-deploy load
    else
        echo "Warning: Image $image_name not found locally. Trying alternative names..."
        
        # Try with fogcam prefix for pipeline services
        if [ "$service" = "pipeline" ] && docker image inspect "fogcam-pipeline:latest" >/dev/null 2>&1; then
            echo "Found fogcam-pipeline:latest, tagging and transferring..."
            docker tag fogcam-pipeline:latest "$image_name"
            docker save "$image_name" | docker --context k8s-deploy load
        elif [ "$service" = "pipeline-frontend" ] && docker image inspect "fogcam-pipeline-frontend:latest" >/dev/null 2>&1; then
            echo "Found fogcam-pipeline-frontend:latest, tagging and transferring..."
            docker tag fogcam-pipeline-frontend:latest "$image_name"
            docker save "$image_name" | docker --context k8s-deploy load
        else
            echo "Error: Could not find image for $service"
            echo "Available images:"
            docker images
            exit 1
        fi
    fi
done

# Step 5: Update K8s manifests with correct image names
echo "Step 5: Updating K8s manifests..."
for file in k8s/*.yaml; do
    # Create backup
    cp "$file" "${file}.bak"
    # Update image names from karlcam/service:latest to karlcam-service:latest
    sed -i 's|image: karlcam/\([^:]*\):latest|image: karlcam-\1:latest|g' "$file"
done

# Step 6: Deploy to K8s cluster
echo "Step 6: Deploying to K8s cluster..."
ssh ubuntu@$K8S_HOST "mkdir -p /tmp/karlcam-k8s"
scp k8s/*.yaml ubuntu@$K8S_HOST:/tmp/karlcam-k8s/

ssh ubuntu@$K8S_HOST << 'EOF'
    echo "Applying K8s manifests..."
    sudo kubectl apply -f /tmp/karlcam-k8s/
    
    echo "Waiting for deployments..."
    sudo kubectl -n karlcam wait --for=condition=available --timeout=300s deployment --all || true
    
    echo ""
    echo "=== Deployment Status ==="
    sudo kubectl -n karlcam get all
    
    echo ""
    echo "=== Service Endpoints ==="
    sudo kubectl -n karlcam get svc
    
    echo ""
    echo "=== Pod Status ==="
    sudo kubectl -n karlcam get pods -o wide
    
    # Clean up temp files
    rm -rf /tmp/karlcam-k8s
EOF

# Step 7: Cleanup
echo "Step 7: Cleanup..."
docker context use default
docker context rm k8s-deploy 2>/dev/null || true
rm -f k8s/*.yaml.bak

echo ""
echo "=== Deployment Complete! ==="
echo "Public frontend should be accessible via LoadBalancer IP"
echo "Check the service endpoints above for the external IP"