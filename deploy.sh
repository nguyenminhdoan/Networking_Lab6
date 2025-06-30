#!/bin/bash
set -euo pipefail

# Usage check
if [[ $# -ne 1 ]]; then
  echo "❌ Usage: $0 <dev|prod>"
  exit 1
fi

ENV="$1"
if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
  echo "❌ Invalid environment: $ENV (must be 'dev' or 'prod')"
  exit 1
fi

STACK_NAME="${ENV}-image-api-backend"
REGION="us-east-1"
SSM_PREFIX="/image-api/${ENV}"

export AWS_PROFILE=personal

echo "🔧 Building SAM app..."
sam build

echo "🔐 Fetching parameters from SSM for $ENV..."

get_param() {
  aws ssm get-parameter \
    --name "$SSM_PREFIX/$1" \
    --with-decryption \
    --query Parameter.Value \
    --output text
}

# Required params

echo "🚀 Deploying to AWS..."
sam deploy \
  --profile personal\
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --confirm-changeset \
  --no-fail-on-empty-changeset \
  --resolve-s3 \
  --parameter-overrides \
    StageName="$ENV" \
