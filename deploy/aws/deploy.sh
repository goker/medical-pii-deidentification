#!/bin/bash
# AWS Lambda Deployment Script for Medical PII De-identification
# Uses AWS SAM (Serverless Application Model)

set -e

# Configuration
STACK_NAME="${STACK_NAME:-medical-pii-removal}"
REGION="${AWS_REGION:-us-east-1}"
STAGE="${STAGE:-prod}"
S3_BUCKET="${S3_BUCKET:-}"  # Will be created if not provided

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Medical PII De-identification - AWS Deploy${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

if ! command -v sam &> /dev/null; then
    echo -e "${RED}Error: AWS SAM CLI is not installed${NC}"
    echo "Install: pip install aws-sam-cli"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

echo -e "${GREEN}Prerequisites OK${NC}"

# Create S3 bucket for deployment artifacts if not provided
if [ -z "$S3_BUCKET" ]; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    S3_BUCKET="sam-artifacts-${ACCOUNT_ID}-${REGION}"

    echo -e "\n${YELLOW}Creating S3 bucket for artifacts: ${S3_BUCKET}${NC}"
    aws s3 mb "s3://${S3_BUCKET}" --region "$REGION" 2>/dev/null || true
fi

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$PROJECT_ROOT"

# Create Lambda handler wrapper
echo -e "\n${YELLOW}Creating Lambda handler...${NC}"
cat > lambda_handler.py << 'EOF'
"""
AWS Lambda handler wrapper for FastAPI application.
Uses Mangum for ASGI-to-Lambda translation.
"""

from mangum import Mangum
from api.main import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")
EOF

# Add mangum to requirements if not present
if ! grep -q "mangum" requirements.txt; then
    echo "mangum>=0.17.0" >> requirements.txt
fi

# Build the application
echo -e "\n${YELLOW}Building SAM application...${NC}"
sam build \
    --template-file deploy/aws/template.yaml \
    --use-container \
    --build-dir .aws-sam/build

# Deploy the application
echo -e "\n${YELLOW}Deploying to AWS...${NC}"
sam deploy \
    --template-file .aws-sam/build/template.yaml \
    --stack-name "${STACK_NAME}-${STAGE}" \
    --s3-bucket "$S3_BUCKET" \
    --s3-prefix "$STACK_NAME" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides Stage="$STAGE" \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

# Get the API endpoint
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-${STAGE}" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)

echo -e "\n${GREEN}API Endpoint:${NC} ${API_ENDPOINT}"
echo -e "\n${YELLOW}Test the API:${NC}"
echo "curl -X POST '${API_ENDPOINT}/api/v1/detect' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"text\": \"Patient John Smith SSN 123-45-6789\"}'"

echo -e "\n${YELLOW}Health Check:${NC}"
echo "curl '${API_ENDPOINT}/api/v1/health'"
