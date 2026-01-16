#!/bin/bash
# Google Cloud Run Deployment Script for Medical PII De-identification

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-medical-pii-removal}"
MODE="${MODE:-api}"  # api or ui

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Medical PII De-identification - GCP Deploy${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 &> /dev/null; then
    echo -e "${RED}Error: Not logged in to gcloud${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi

# Get or set project ID
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}Error: No GCP project ID set${NC}"
        echo "Run: gcloud config set project YOUR_PROJECT_ID"
        echo "Or: export GCP_PROJECT_ID=your-project-id"
        exit 1
    fi
fi

echo -e "${GREEN}Using project: ${PROJECT_ID}${NC}"
echo -e "${GREEN}Deploying to: ${REGION}${NC}"

# Enable required APIs
echo -e "\n${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    --project="$PROJECT_ID"

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$PROJECT_ROOT"

# Build and push Docker image
echo -e "\n${YELLOW}Building Docker image...${NC}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

gcloud builds submit \
    --tag "${IMAGE_NAME}:latest" \
    --project="$PROJECT_ID" \
    --timeout=1800s

# Deploy to Cloud Run
echo -e "\n${YELLOW}Deploying to Cloud Run...${NC}"

gcloud run deploy "$SERVICE_NAME" \
    --image "${IMAGE_NAME}:latest" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 60s \
    --concurrency 10 \
    --min-instances 0 \
    --max-instances 5 \
    --allow-unauthenticated \
    --set-env-vars "PRELOAD_MODEL=true,MODE=${MODE}"

# Get the service URL
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format 'value(status.url)')

echo -e "\n${GREEN}Service URL:${NC} ${SERVICE_URL}"

echo -e "\n${YELLOW}Test the API:${NC}"
echo "curl -X POST '${SERVICE_URL}/api/v1/detect' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"text\": \"Patient John Smith SSN 123-45-6789\"}'"

echo -e "\n${YELLOW}Health Check:${NC}"
echo "curl '${SERVICE_URL}/api/v1/health'"
