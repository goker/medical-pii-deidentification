# Azure Container Apps Deployment

Deploy the Medical PII De-identification API to Azure Container Apps.

## Free Tier Limits

- **Azure Container Apps**: 180,000 vCPU-seconds/month, 360,000 GB-seconds/month free
- **Azure Container Registry (Basic)**: First 5 GB storage free

## Prerequisites

1. **Azure CLI** installed
   ```bash
   # macOS
   brew install azure-cli

   # Or download from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
   ```

2. **Login to Azure**
   ```bash
   az login
   ```

3. **Set subscription (if multiple)**
   ```bash
   az account set --subscription YOUR_SUBSCRIPTION_ID
   ```

## Quick Deploy

```bash
# From project root
chmod +x deploy/azure/deploy.sh
./deploy/azure/deploy.sh
```

## Configuration

Set environment variables before deployment:

```bash
export AZURE_RESOURCE_GROUP=my-pii-rg    # Resource group name
export AZURE_LOCATION=eastus              # Azure region
export APP_NAME=medical-pii-removal       # Container App name
export ACR_NAME=mypiiregistry             # Container Registry name (globally unique)
```

## Manual Deployment

1. **Create resource group**
   ```bash
   az group create --name medical-pii-rg --location eastus
   ```

2. **Create Azure Container Registry**
   ```bash
   az acr create --resource-group medical-pii-rg --name yourregistryname --sku Basic --admin-enabled true
   ```

3. **Build and push image**
   ```bash
   az acr build --registry yourregistryname --image medical-pii-removal:latest .
   ```

4. **Deploy Container App**
   ```bash
   az containerapp create \
     --name medical-pii-removal \
     --resource-group medical-pii-rg \
     --image yourregistryname.azurecr.io/medical-pii-removal:latest \
     --target-port 8000 \
     --ingress external \
     --cpu 1 --memory 2Gi \
     --min-replicas 0 --max-replicas 5
   ```

## Testing

```bash
# Get app URL
APP_URL=$(az containerapp show --name medical-pii-removal --resource-group medical-pii-rg --query properties.configuration.ingress.fqdn -o tsv)

# Health check
curl "https://${APP_URL}/api/v1/health"

# Detect PII
curl -X POST "https://${APP_URL}/api/v1/detect" \
  -H 'Content-Type: application/json' \
  -d '{"text": "Patient John Smith DOB 03/15/1985 SSN 123-45-6789"}'

# De-identify
curl -X POST "https://${APP_URL}/api/v1/deidentify" \
  -H 'Content-Type: application/json' \
  -d '{"text": "Patient John Smith DOB 03/15/1985", "strategy": "placeholder"}'
```

## Deploy UI Version

Modify the ARM template or use az cli:
```bash
az containerapp update \
  --name medical-pii-removal \
  --resource-group medical-pii-rg \
  --set-env-vars MODE=ui
```

## Cleanup

```bash
# Delete all resources in the resource group
az group delete --name medical-pii-rg --yes --no-wait
```

## Azure-Specific Features

### HIPAA Compliance

Azure offers HIPAA BAA (Business Associate Agreement) for healthcare workloads:
- Enable Azure Security Center
- Use Azure Key Vault for secrets
- Enable diagnostic logging
- Consider Azure API Management for additional security

### Scaling Configuration

Container Apps settings:
- **CPU**: 1 vCPU
- **Memory**: 2 GB
- **Min replicas**: 0 (scales to zero)
- **Max replicas**: 5
- **Concurrent requests**: 10/instance

### Cost Estimate

For typical usage (10,000 requests/month):
- **Container Apps**: Free tier (under 180,000 vCPU-seconds)
- **Container Registry**: ~$5/month (Basic tier)
- **Log Analytics**: ~$2.76/GB ingested
- **Estimated Cost**: $5-10/month
