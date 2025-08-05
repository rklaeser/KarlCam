#!/bin/bash
# Deploy KarlCam to K3s cluster using existing build server pattern

set -e

# Configuration - matches your GitHub Actions
DOCKER_HOST="${DOCKER_HOST:-tcp://10.0.0.35:2375}"
K8S_HOST="${K8S_HOST:-10.0.0.40}"
NAMESPACE="karlcam"

echo "=== KarlCam K8s Deployment ==="
echo "Docker Host: $DOCKER_HOST"
echo "K8s Host: $K8S_HOST"

# Set up Docker context (same as GitHub Actions)
docker context create k8s-deploy --docker host=$DOCKER_HOST || true
docker context use k8s-deploy

# Update K8s manifests to use your existing image names
echo "Updating manifests with correct image names..."
for file in k8s/*.yaml; do
    # Change from karlcam/service:latest to karlcam-service:latest (matching your pattern)
    sed -i.bak 's|image: karlcam/\([^:]*\):latest|image: karlcam-\1:latest|g' $file
done

# Deploy to K8s cluster
echo "Deploying to K8s cluster..."
ssh ubuntu@$K8S_HOST "mkdir -p /tmp/karlcam-k8s"
scp k8s/*.yaml ubuntu@$K8S_HOST:/tmp/karlcam-k8s/

ssh ubuntu@$K8S_HOST << 'EOF'
    echo "Applying K8s manifests..."
    sudo kubectl apply -f /tmp/karlcam-k8s/
    
    echo "Waiting for deployments..."
    sudo kubectl -n karlcam wait --for=condition=available --timeout=300s deployment --all || true
    
    echo "Deployment status:"
    sudo kubectl -n karlcam get all
    
    echo "Getting service IPs:"
    sudo kubectl -n karlcam get svc
EOF

echo "Deployment complete!"

# Cleanup
docker context use default
docker context rm k8s-deploy || true
rm -f k8s/*.yaml.bak