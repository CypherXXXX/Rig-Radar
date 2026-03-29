#!/bin/bash

set -e

STACK_NAME="rigradar-stack"
REGION="us-east-1"
S3_BUCKET=""

echo "=========================================="
echo "  RigRadar Deployment"
echo "=========================================="

if [ -z "$S3_BUCKET" ]; then
    echo "Creating S3 bucket for SAM artifacts..."
    S3_BUCKET="rigradar-sam-artifacts-$(date +%s)"
    aws s3 mb "s3://$S3_BUCKET" --region "$REGION" 2>/dev/null || true
fi

echo "Installing backend dependencies..."
cd ../backend
pip install -r requirements.txt -t .

echo "Installing worker dependencies..."
cd ../worker
pip install -r requirements.txt -t .

echo "Building SAM application..."
cd ../infrastructure
sam build --template-file template.yaml

echo "Deploying SAM application..."
sam deploy \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --s3-bucket "$S3_BUCKET" \
    --capabilities CAPABILITY_IAM \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="

API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
    --output text)

echo "API Endpoint: $API_ENDPOINT"
echo ""
echo "Next steps:"
echo "  1. Set NEXT_PUBLIC_API_URL=$API_ENDPOINT in your Vercel environment"
echo "  2. Deploy the frontend: cd frontend && vercel --prod"
echo "  3. Configure Clerk webhook endpoint"
