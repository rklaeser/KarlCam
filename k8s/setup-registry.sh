#!/bin/bash
# Configure K3s nodes to pull from your Docker build server

DOCKER_REGISTRY_HOST="10.0.0.35:5000"
K3S_NODES="10.0.0.40 10.0.0.45 10.0.0.46 10.0.0.47"

echo "Setting up Docker registry access on K3s nodes..."

for node in $K3S_NODES; do
    echo "Configuring node: $node"
    
    ssh ubuntu@$node << EOF
        # Create K3s registry config
        sudo mkdir -p /etc/rancher/k3s
        sudo tee /etc/rancher/k3s/registries.yaml > /dev/null <<EOL
mirrors:
  "10.0.0.35:5000":
    endpoint:
      - "http://10.0.0.35:5000"
configs:
  "10.0.0.35:5000":
    tls:
      insecure_skip_verify: true
EOL
        
        # Restart K3s to apply registry config
        if [ -f /etc/systemd/system/k3s.service ]; then
            sudo systemctl restart k3s
        else
            sudo systemctl restart k3s-agent
        fi
        
        echo "Registry configured on $node"
EOF
done

echo "Registry setup complete!"