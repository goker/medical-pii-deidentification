# AWS Lambda Deployment

Deploy the Medical PII De-identification API to AWS Lambda with API Gateway.

## Free Tier Limits

- **Lambda**: 1 million free requests/month, 400,000 GB-seconds compute
- **API Gateway**: 1 million API calls/month

## Prerequisites

1. **AWS CLI** installed and configured
   ```bash
   aws configure
   ```

2. **AWS SAM CLI** installed
   ```bash
   pip install aws-sam-cli
   ```

3. **Docker** installed (for building)

## Quick Deploy

```bash
# From project root
chmod +x deploy/aws/deploy.sh
./deploy/aws/deploy.sh
```

## Configuration

Set environment variables before deployment:

```bash
export STACK_NAME=my-pii-api        # Stack name (default: medical-pii-removal)
export AWS_REGION=us-east-1         # AWS region
export STAGE=prod                   # prod, staging, or dev
```

## Manual Deployment

1. **Build the application**
   ```bash
   sam build --template-file deploy/aws/template.yaml --use-container
   ```

2. **Deploy**
   ```bash
   sam deploy --guided
   ```

3. **Get API endpoint**
   ```bash
   aws cloudformation describe-stacks \
     --stack-name medical-pii-removal-prod \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
     --output text
   ```

## Testing

```bash
# Health check
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/api/v1/health

# Detect PII
curl -X POST 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/api/v1/detect' \
  -H 'Content-Type: application/json' \
  -d '{"text": "Patient John Smith DOB 03/15/1985 SSN 123-45-6789"}'

# De-identify
curl -X POST 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/api/v1/deidentify' \
  -H 'Content-Type: application/json' \
  -d '{"text": "Patient John Smith DOB 03/15/1985", "strategy": "placeholder"}'
```

## Cleanup

```bash
sam delete --stack-name medical-pii-removal-prod
```

## Cold Start Optimization

The Lambda function is configured with:
- **Memory**: 1024 MB (fits the 44M model)
- **Ephemeral Storage**: 2 GB
- **Timeout**: 60 seconds

First request after cold start takes ~10-15 seconds for model loading.
Subsequent requests are much faster (~100-500ms).

## Cost Estimate

For typical usage (10,000 requests/month):
- **Lambda**: Free tier (under 1M requests)
- **API Gateway**: Free tier (under 1M requests)
- **Estimated Cost**: $0/month
