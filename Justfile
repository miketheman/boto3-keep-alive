# Justfile for boto3-keep-alive
# Automation commands for SAM CLI operations

# Default recipe - list all available commands
default:
    @just --list

# Run all checks (lint, format check, typecheck)
check:
    ruff check .
    ruff format --check .
    ty check

# Run linter and auto-fix issues, then format code
fix:
    ruff check --fix .
    ruff format .

# Validate SAM template syntax and run linting
validate:
    sam validate --lint

# Build the Lambda function package with uv-generated requirements
build:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Generating requirements.txt from pyproject.toml..."
    uv pip compile pyproject.toml --output-file src/requirements.txt --no-header --no-annotate
    echo "Building with SAM..."
    sam build
    echo "Cleaning up requirements.txt..."
    rm src/requirements.txt
    echo "Build complete!"

# Deploy to AWS (uses saved configuration from samconfig.toml)
deploy: build
    sam deploy

# Deploy to AWS with guided setup (first time deployment)
deploy-guided: build
    sam deploy --guided

# Build and deploy in one command
ship: check build deploy

# Test function locally with sample event (requires DynamoDB Local running)
test-local: build dynamodb-local
    sam local invoke PostsFunction \
        --event events/sample-post.json \
        --env-vars '{"PostsFunction":{"AWS_ENDPOINT_URL_DYNAMODB":"http://host.docker.internal:8000"}}'

# Tail CloudWatch logs for the Lambda function (optionally filter by string)
[arg("filter", long)]
logs filter="DynamoDb.put_item":
    sam logs --stack-name boto3-keep-alive --tail --filter "{{filter}}"

# Show stack status and outputs
info:
    @echo "Stack Status:"
    @aws cloudformation describe-stacks \
        --stack-name boto3-keep-alive \
        --query 'Stacks[0].StackStatus' \
        --output text \
        --no-cli-pager
    @echo "\nStack Outputs:"
    @aws cloudformation describe-stacks \
        --stack-name boto3-keep-alive \
        --query 'Stacks[0].Outputs' \
        --output table \
        --no-cli-pager

# Run load test against deployed function
[arg("num", long, short = 'n')]
[arg("concurrency", long, short = 'c')]
[arg("delay", long, short = 'd')]
load-test num="10" concurrency="1" delay="0":
    @FUNCTION_URL=$(aws cloudformation describe-stacks \
        --stack-name boto3-keep-alive \
        --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
        --output text \
        --no-cli-pager) && \
        echo $FUNCTION_URL && \
    ./scripts/load-test.py $FUNCTION_URL -n {{num}} -c {{concurrency}} -d {{delay}}

# Send a single test request to the deployed function
[arg("message", long, short = 'm')]
test-remote message="Test from just command":
    #!/usr/bin/env bash
    set -euo pipefail
    FUNCTION_URL=$(aws cloudformation describe-stacks \
        --stack-name boto3-keep-alive \
        --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
        --output text --no-cli-pager)
    echo "Testing: $FUNCTION_URL"
    curl -s -X POST "$FUNCTION_URL" \
        -H "Content-Type: application/json" \
        -d '{"user_id": "just-test", "message": "{{message}}"}' \
        | python3 -m json.tool

# Delete all AWS resources (cleanup)
destroy:
    sam delete --no-prompts

# Start DynamoDB Local in Docker (automatically creates the table)
dynamodb-local:
    ./scripts/start-dynamodb-local.sh

# Stop DynamoDB Local
dynamodb-local-stop:
    docker stop dynamodb-local || true
