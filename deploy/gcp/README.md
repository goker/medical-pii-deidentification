# Google Cloud Run Deployment

Deploy the Medical PII De-identification API to Google Cloud Run.

## Free Tier Limits

- **Cloud Run**: 2 million requests/month, 180,000 vCPU-seconds, 360,000 GB-seconds
- **Container Registry**: 0.5 GB storage free

## Prerequisites

1. **Google Cloud SDK** installed
   ```bash
   # macOS
   brew install google-cloud-sdk

   # Or download from https://cloud.google.com/sdk/docs/install
   ```

2. **Initialize and authenticate**
   ```bash
   gcloud init
   gcloud auth login
   ```

3. **Set your project**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

## Quick Deploy

```bash
# From project root
chmod +x deploy/gcp/deploy.sh
./deploy/gcp/deploy.sh
```

## Configuration

Set environment variables before deployment:

```bash
export GCP_PROJECT_ID=my-project     # GCP project ID
export GCP_REGION=us-central1        # Region (default: us-central1)
export SERVICE_NAME=medical-pii-api  # Service name
export MODE=api                      # api or ui
```

## Manual Deployment

1. **Enable APIs**
   ```bash
   gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com
   ```

2. **Build and push image**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/medical-pii-removal
   ```

3. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy medical-pii-removal \
     --image gcr.io/YOUR_PROJECT_ID/medical-pii-removal \
     --platform managed \
     --region us-central1 \
     --memory 1Gi \
     --allow-unauthenticated
   ```

## Testing

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe medical-pii-removal \
  --platform managed --region us-central1 --format 'value(status.url)')

# Health check
curl "${SERVICE_URL}/api/v1/health"

# Detect PII
curl -X POST "${SERVICE_URL}/api/v1/detect" \
  -H 'Content-Type: application/json' \
  -d '{"text": "Patient John Smith DOB 03/15/1985 SSN 123-45-6789"}'

# De-identify
curl -X POST "${SERVICE_URL}/api/v1/deidentify" \
  -H 'Content-Type: application/json' \
  -d '{"text": "Patient John Smith DOB 03/15/1985", "strategy": "placeholder"}'
```

## Deploy UI Version

```bash
export MODE=ui
./deploy/gcp/deploy.sh
```

## Cleanup

```bash
# Delete Cloud Run service
gcloud run services delete medical-pii-removal --region us-central1

# Delete container images
gcloud container images delete gcr.io/YOUR_PROJECT_ID/medical-pii-removal --force-delete-tags
```

## Cold Start Optimization

Cloud Run settings:
- **Memory**: 1 GB
- **CPU**: 1 vCPU
- **Concurrency**: 10 requests/instance
- **Min instances**: 0 (scales to zero for cost savings)
- **Max instances**: 5

First request after cold start: ~10-15 seconds
Subsequent requests: ~100-300ms

## Cost Estimate

For typical usage (10,000 requests/month):
- **Cloud Run**: Free tier (under 2M requests)
- **Container Registry**: ~$0.026/GB/month
- **Estimated Cost**: $0-1/month
