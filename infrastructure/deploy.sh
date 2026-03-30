#!/bin/bash

set -e

STACK_NAME="rigradar-stack"
REGION="us-east-1"

echo "=========================================="
echo "  RigRadar Deployment"
echo "=========================================="

echo "Building SAM application..."
cd infrastructure
sam build --template-file template.yaml

echo "Deploying SAM application..."
sam deploy

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
