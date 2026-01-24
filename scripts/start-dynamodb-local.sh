#!/bin/bash
set -e

echo "Starting DynamoDB Local..."

# Start DynamoDB Local in the background
docker run -d --rm --name dynamodb-local -p 8000:8000 amazon/dynamodb-local

echo "Waiting for DynamoDB Local to be ready..."
sleep 3

# Check if table already exists
TABLE_EXISTS=$(aws dynamodb list-tables \
  --endpoint-url http://localhost:8000 \
  --region us-east-2 \
  --query "TableNames[?@=='keepalive-test']" \
  --output text 2>/dev/null || echo "")

if [ -z "$TABLE_EXISTS" ]; then
  echo "Creating table 'keepalive-test'..."
  aws dynamodb create-table \
    --table-name keepalive-test \
    --attribute-definitions AttributeName=postId,AttributeType=S \
    --key-schema AttributeName=postId,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url http://localhost:8000 \
    --region us-east-2 \
    --no-cli-pager
  echo "✓ Table created successfully"
else
  echo "✓ Table 'keepalive-test' already exists"
fi

echo ""
echo "DynamoDB Local is running on http://localhost:8000"
echo "To stop: docker stop dynamodb-local"
echo ""
echo "View logs: docker logs -f dynamodb-local"
