#!/bin/bash
# Deploy KarlCam to K3s cluster

set -e

echo "=== KarlCam Deployment Script ==="

# Configuration
REGISTRY="${DOCKER_REGISTRY:-docker.io}"
NAMESPACE="karlcam"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Function to build and push images
build_and_push() {
    local service=$1
    local dockerfile=$2
    
    echo "Building $service..."
    docker build -t $REGISTRY/karlcam/$service:$IMAGE_TAG -f $dockerfile .
    
    echo "Pushing $service..."
    docker push $REGISTRY/karlcam/$service:$IMAGE_TAG
}

# Build and push all images
echo "1. Building and pushing Docker images..."
build_and_push "pipeline" "pipeline/Dockerfile"
build_and_push "backend" "backend/Dockerfile"
build_and_push "public-frontend" "public-frontend/Dockerfile"
build_and_push "pipeline-frontend" "pipeline-frontend/Dockerfile"

echo ""
echo "2. Deploying to Kubernetes..."

# Update image tags in manifests
for file in k8s/*.yaml; do
    sed -i.bak "s|image: karlcam/|image: $REGISTRY/karlcam/|g" $file
    sed -i.bak "s|:latest|:$IMAGE_TAG|g" $file
done

# Apply manifests
kubectl apply -f k8s/

echo ""
echo "3. Waiting for deployments..."
kubectl -n $NAMESPACE wait --for=condition=available --timeout=300s deployment --all

echo ""
echo "4. Deployment status:"
kubectl -n $NAMESPACE get all

echo ""
echo "5. Service URLs:"
echo "Public Frontend: $(kubectl -n $NAMESPACE get svc karlcam-public-frontend -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"

echo ""
echo "Deployment complete!"