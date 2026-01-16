#!/bin/bash
# Azure Container Apps Deployment Script for Medical PII De-identification

set -e

# Configuration
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-medical-pii-rg}"
LOCATION="${AZURE_LOCATION:-eastus}"
APP_NAME="${APP_NAME:-medical-pii-removal}"
ACR_NAME="${ACR_NAME:-medicalpiiremovalacr}"  # Must be globally unique

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Medical PII De-identification - Azure Deploy${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed${NC}"
    echo "Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${RED}Error: Not logged in to Azure${NC}"
    echo "Run: az login"
    exit 1
fi

echo -e "${GREEN}Prerequisites OK${NC}"

# Get subscription info
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "${GREEN}Using subscription: ${SUBSCRIPTION_ID}${NC}"

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$PROJECT_ROOT"

# Create resource group
echo -e "\n${YELLOW}Creating resource group...${NC}"
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none

# Create Azure Container Registry
echo -e "\n${YELLOW}Creating Azure Container Registry...${NC}"
# Make ACR name unique by adding random suffix
ACR_NAME="${ACR_NAME}$(date +%s | tail -c 5)"
az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku Basic \
    --admin-enabled true \
    --output none

# Get ACR credentials
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query passwords[0].value -o tsv)

# Build and push Docker image
echo -e "\n${YELLOW}Building and pushing Docker image...${NC}"
az acr build \
    --registry "$ACR_NAME" \
    --image "${APP_NAME}:latest" \
    --file Dockerfile \
    . \
    --no-logs

# Install/upgrade Container Apps extension
echo -e "\n${YELLOW}Installing Container Apps extension...${NC}"
az extension add --name containerapp --upgrade --yes

# Register required providers
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait

# Deploy using ARM template
echo -e "\n${YELLOW}Deploying to Azure Container Apps...${NC}"
az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file deploy/azure/azure-deploy.json \
    --parameters containerAppName="$APP_NAME" \
    --parameters containerImage="${ACR_LOGIN_SERVER}/${APP_NAME}:latest" \
    --parameters containerRegistryServer="$ACR_LOGIN_SERVER" \
    --parameters containerRegistryUsername="$ACR_USERNAME" \
    --parameters containerRegistryPassword="$ACR_PASSWORD" \
    --output none

# Get the app URL
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

APP_URL=$(az containerapp show \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query properties.configuration.ingress.fqdn -o tsv)

APP_URL="https://${APP_URL}"

echo -e "\n${GREEN}App URL:${NC} ${APP_URL}"

echo -e "\n${YELLOW}Test the API:${NC}"
echo "curl -X POST '${APP_URL}/api/v1/detect' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"text\": \"Patient John Smith SSN 123-45-6789\"}'"

echo -e "\n${YELLOW}Health Check:${NC}"
echo "curl '${APP_URL}/api/v1/health'"

echo -e "\n${YELLOW}Azure Resources Created:${NC}"
echo "- Resource Group: ${RESOURCE_GROUP}"
echo "- Container Registry: ${ACR_NAME}"
echo "- Container App: ${APP_NAME}"
