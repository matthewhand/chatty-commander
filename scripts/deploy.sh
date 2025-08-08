#!/bin/bash

# ChattyCommander Production Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="chatty-commander"
TAG="${TAG:-latest}"
REGISTRY="${REGISTRY:-}"
FULL_IMAGE_NAME="${REGISTRY}${IMAGE_NAME}:${TAG}"

echo -e "${GREEN}🚀 ChattyCommander Production Deployment${NC}"
echo "=========================================="

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed.${NC}" >&2; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}kubectl is required but not installed.${NC}" >&2; exit 1; }

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t "${FULL_IMAGE_NAME}" .

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
docker run --rm "${FULL_IMAGE_NAME}" python -m pytest -q

# Push to registry if specified
if [ -n "${REGISTRY}" ]; then
    echo -e "${YELLOW}Pushing to registry...${NC}"
    docker push "${FULL_IMAGE_NAME}"
fi

# Deploy to Kubernetes
echo -e "${YELLOW}Deploying to Kubernetes...${NC}"

# Create namespace if it doesn't exist
kubectl create namespace chatty-commander --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubernetes manifests
kubectl apply -f k8s/deployment.yaml -n chatty-commander

# Wait for deployment to be ready
echo -e "${YELLOW}Waiting for deployment to be ready...${NC}"
kubectl rollout status deployment/chatty-commander -n chatty-commander --timeout=300s

# Get service URL
echo -e "${YELLOW}Getting service information...${NC}"
kubectl get service chatty-commander-service -n chatty-commander

# Health check
echo -e "${YELLOW}Performing health check...${NC}"
SERVICE_IP=$(kubectl get service chatty-commander-service -n chatty-commander -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -n "${SERVICE_IP}" ]; then
    curl -f "http://${SERVICE_IP}/api/v1/status" || echo -e "${RED}Health check failed${NC}"
else
    echo -e "${YELLOW}Service IP not available yet. Use port-forward to test:${NC}"
    echo "kubectl port-forward service/chatty-commander-service 8100:80 -n chatty-commander"
fi

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Access your application at: http://localhost:8100${NC}"
echo -e "${GREEN}📊 Monitor with: kubectl logs -f deployment/chatty-commander -n chatty-commander${NC}"
