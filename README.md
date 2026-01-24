# boto3-keep-alive

A Lambda function that handles POST requests and persists data to DynamoDB, built with AWS SAM (Serverless Application Model).

This project demonstrates modern AWS development practices using native AWS tooling, Python 3.14 runtime, ARM64 architecture, and Infrastructure as Code best practices.

But more specifically, how to set TCP Keep Alive for Python-based Lambda functions.
Read more at <https://www.miketheman.net/2022/10/04/reduce-aws-lambda-latencies-with-keep-alive-in-python/>

## Architecture

```
HTTP Client → Lambda Function URL → Lambda Function (Python 3.14 / ARM64) → DynamoDB Table
```

- **Lambda Function**: Processes POST requests with user_id and message (ARM64 architecture)
- **DynamoDB Table**: Stores posts with post_id as primary key
- **Function URL**: Public HTTPS endpoint (no authentication required)

### Why ARM64?

This project uses AWS Graviton2 processors (ARM64 architecture) for:
- **20% better price-performance** compared to x86_64
- **Lower latency** and improved energy efficiency
- **Native compatibility** with Apple Silicon (M1/M2/M3) development machines
- **Seamless deployment** from ARM-based CI/CD runners

## Prerequisites

Before you begin, ensure you have the following installed:

- **AWS CLI**: [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
  ```bash
  aws --version  # Should be 2.x or higher
  ```

- **SAM CLI**: [Installation Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
  ```bash
  sam --version  # Should be 1.100.0 or higher
  ```

- **Just**: Command runner for automation [Installation Guide](https://github.com/casey/just#installation)
  ```bash
  just --version
  ```

- **uv**: Fast Python package manager (optional, for development) [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
  ```bash
  uv --version
  ```

- **uv**: Fast Python package manager (optional, for development) [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
  ```bash
  uv --version
  ```

- **Docker**: Required for local testing (optional)
  ```bash
  docker --version
  ```

## Development Setup

This project uses modern Python tooling for development:

- **uv**: Fast Python package manager and environment manager
- **ruff**: Fast linter and formatter (replaces black, flake8, isort)
- **ty**: Fast type checker from Astral (replaces mypy)

### Install Development Dependencies

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install development dependencies
uv sync --group dev
```

### Code Quality Commands

```bash
# Run all checks (lint, format check, type check)
just check

# Run linter and auto-fix issues, then format code
just fix
```

These commands use:
- **ruff check**: Linting with rules for pycodestyle, pyflakes, isort, flake8-bugbear, comprehensions, and pyupgrade
- **ruff format**: Code formatting (compatible with black)
- **ty check**: Type checking (faster alternative to mypy)

- **AWS Credentials**: Configure your AWS credentials
  ```bash
  aws configure
  ```

## Development Setup

This project uses modern Python tooling for development:

- **uv**: Fast Python package manager and environment manager
- **ruff**: Fast linter and formatter (replaces black, flake8, isort)
- **ty**: Fast type checker from Astral (replaces mypy)

### Install Development Dependencies

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install development dependencies
uv sync --group dev
```

### Code Quality Commands

```bash
# Run all checks (lint, format check, type check)
just check

# Run linter and auto-fix issues, then format code
just fix
```

These commands use:
- **ruff check**: Linting with rules for pycodestyle, pyflakes, isort, flake8-bugbear, comprehensions, and pyupgrade
- **ruff format**: Code formatting (compatible with black)
- **ty check**: Type checking (faster alternative to mypy)

## IAM Permissions

To deploy, monitor, debug, and remove this stack, you need specific IAM permissions. A least-privilege IAM policy is provided in `iam-policy.json`.

### Required Permissions

The policy grants permissions for:

- **CloudFormation**: Create, update, delete, and describe stacks
- **Lambda**: Manage functions, function URLs, and configurations
- **DynamoDB**: Create, update, delete, and describe tables
- **S3**: Store deployment artifacts in SAM-managed buckets
- **IAM**: Create and manage Lambda execution roles
- **CloudWatch Logs**: View logs for monitoring and debugging
- **CloudWatch Metrics**: Monitor function performance
- **X-Ray**: Enable distributed tracing for debugging

### Applying the Policy

**Before deploying, you must attach this policy to your IAM user or role.**

**Option 1: Attach to an IAM User (for local development)**

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create the policy
aws iam create-policy \
  --policy-name Boto3KeepAliveDeployPolicy \
  --policy-document file://iam-policy.json \

### IAM Permissions for AWS Lambda Power Tuning

If you want to use [AWS Lambda Power Tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning) to optimize your function's memory configuration, you'll need additional IAM permissions.

The `iam-policy.json` file includes permissions for Power Tuning resources (prefixed with `aws-lambda-power-tuning-*`). These allow CloudFormation to create:
- IAM roles for the Power Tuning state machine and Lambda functions
- Step Functions state machine
- Lambda functions and layers
- CloudWatch log groups

If you've already attached the policy, you're ready to deploy Power Tuning. If not, update your IAM policy:

```bash
# Update the existing policy
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws iam create-policy-version \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/Boto3KeepAliveDeployPolicy \
  --policy-document file://iam-policy.json \
  --set-as-default
```
  --description "Least-privilege policy for deploying boto3-keep-alive stack"

# Attach to your current user (replace YOUR_USERNAME with your IAM username)
YOUR_USERNAME=$(aws sts get-caller-identity --query 'Arn' --output text | cut -d'/' -f2)
aws iam attach-user-policy \
  --user-name $YOUR_USERNAME \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/Boto3KeepAliveDeployPolicy

echo "Policy attached to user: $YOUR_USERNAME"
```

**Option 2: Attach to an IAM Role (for CI/CD pipelines)**

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create the policy (if not already created)
aws iam create-policy \
  --policy-name Boto3KeepAliveDeployPolicy \
  --policy-document file://iam-policy.json \
  --description "Least-privilege policy for deploying boto3-keep-alive stack"

# Attach to a role (replace YOUR_ROLE_NAME)
aws iam attach-role-policy \
This generates a `requirements.txt` from `pyproject.toml` using uv, builds the Lambda package with SAM, then cleans up the temporary file.
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/Boto3KeepAliveDeployPolicy
```

**Verify the policy is attached:**

```bash
just deploy-guided
aws iam list-attached-user-policies --user-name $YOUR_USERNAME

# For roles
aws iam list-attached-role-policies --role-name YOUR_ROLE_NAME
```

### IAM Permissions for AWS Lambda Power Tuning

If you want to use [AWS Lambda Power Tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning) to optimize your function's memory configuration, you'll need additional IAM permissions.

The `iam-policy.json` file includes permissions for Power Tuning resources (prefixed with `aws-lambda-power-tuning-*`). These allow CloudFormation to create:
- IAM roles for the Power Tuning state machine and Lambda functions
- Step Functions state machine
- Lambda functions and layers
just deploy

If you've already attached the policy, you're ready to deploy Power Tuning. If not, update your IAM policy:


**Build and deploy in one command:**

```bash
just ship
```
```bash
# Update the existing policy
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws iam create-policy-version \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/Boto3KeepAliveDeployPolicy \
  --policy-document file://iam-policy.json \
  --set-as-default
```

### Security Notes

- The policy follows the principle of least privilege
- Resources are scoped to this specific stack (`boto3-keep-alive-*`)
- Some actions require wildcard resources (e.g., CloudWatch metrics, X-Ray tracing)
- Review and adjust the policy based on your organization's security requirements
- Consider using AWS Organizations SCPs for additional guardrails

## Quick Start

### 1. Validate the SAM Template

```bash
just validate
```

This checks the SAM template syntax and runs linting to catch any configuration issues.

### 2. Build the Application

```bash
just build
```

This generates a `requirements.txt` from `pyproject.toml` using uv, builds the Lambda package with SAM, then cleans up the temporary file.

### 3. Deploy to AWS

**First-time deployment** (with guided setup):

```bash
just deploy-guided
```

You'll be prompted for:
- **Stack name**: `boto3-keep-alive` (recommended, or your preferred name)
- **AWS Region**: `us-east-2` (or your preferred region)
- **Confirm changes**: `Y`
- **Allow SAM CLI IAM role creation**: `Y`
- **Save arguments to config**: `Y` (important!)

SAM will save your answers to `samconfig.toml`.

**Subsequent deployments** (using saved configuration):

```bash
just deploy
```

This uses the configuration saved in `samconfig.toml` - no prompts, much faster!

**Build and deploy in one command:**

```bash
just ship
```

### 4. Get Your Function URL

After deployment, the Function URL will be displayed in the outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name serverless-modernization \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text
```

Or check the AWS Console: CloudFormation → Stacks → boto3-keep-alive → Outputs

## Deploying from ARM-Based Runners

This project is optimized for ARM64 architecture and works seamlessly on ARM-based development machines and CI/CD runners.

### Local Development on Apple Silicon (M1/M2/M3)

No special configuration needed! The Lambda function uses ARM64 architecture, which matches your Mac:

```bash
# Build and deploy normally
just build
just deploy
```

SAM CLI automatically detects your ARM architecture and builds compatible packages.

### CI/CD on ARM Runners

**GitHub Actions with ARM runners:**

```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-24.04-arm64  # ARM-based runner
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
          architecture: 'arm64'
      
      - name: Setup SAM CLI
        uses: aws-actions/setup-sam@v2
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::YOUR_ACCOUNT:role/GitHubActionsRole
          aws-region: us-east-2
      
      - name: Build and Deploy
        run: |
          sam build
          sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
```

**GitLab CI with ARM runners:**

```yaml
deploy:
  image: public.ecr.aws/sam/build-python3.14:latest-arm64
  tags:
    - arm64
  script:
    - sam build
    - sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
  only:
    - main
```

- `just test-local` passes the DynamoDB Local endpoint as an environment variable to the Lambda function
```yaml
version: 0.2
phases:
  build:
    commands:
      - sam build
      - sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
environment:
  type: ARM_CONTAINER
  image: aws/codebuild/amazonlinux2-aarch64-standard:3.0
```

### Cross-Architecture Deployment

If you need to deploy from an x86_64 machine to ARM64 Lambda:

```bash
# Use Docker to build for ARM64
sam build --use-container

# Or specify architecture explicitly
sam build --use-container --build-image public.ecr.aws/sam/build-python3.14:latest-arm64
```

### Switching to x86_64

If you need x86_64 instead of ARM64, edit `template.yaml`:

```yaml
Globals:
  Function:
    Architectures:
      - x86_64  # Change from arm64
```

Then rebuild and redeploy:

```bash
just build
just deploy
```

## Testing

### Local Testing

Test the Lambda function locally before deploying to AWS.

**Quick Start with DynamoDB Local:**

```bash
# Terminal 1: Start DynamoDB Local (creates table automatically)
just dynamodb-local

# Terminal 2: Test the function
just test-local
```

That's it! The `just test-local` command automatically configures the function to use DynamoDB Local.

**How it works:**

- `just dynamodb-local` starts DynamoDB Local in Docker and creates the `keepalive-test` table
- `just test-local` passes the DynamoDB Local endpoint as an environment variable to the Lambda function
- The boto3 SDK automatically uses this [service-specific endpoint](https://docs.aws.amazon.com/sdkref/latest/guide/feature-ss-endpoints.html) when creating the DynamoDB client
- `-c, --concurrency`: Number of concurrent workers (default: 1)

**Stop DynamoDB Local:**


**Load test behavior:**
The load test simulates realistic user traffic patterns:
- Uses a queue to dynamically distribute requests across workers
- Worker 0 sends requests as fast as possible (no delay) - simulates a "power user"
- Other workers apply the specified delay between their requests - simulates normal users with "think time"
- All requests complete as quickly as possible since worker 0 isn't throttled
- Example: `-c 5 -d 1000` creates 5 workers where worker 0 fires rapidly and workers 1-4 wait 1 second between requests
```bash
just dynamodb-local-stop
```

**Verify data in DynamoDB Local:**

```bash
# List tables
just dynamodb-local-list

# Scan the table to see inserted records
aws dynamodb scan \
  --table-name keepalive-test \
  --endpoint-url http://localhost:8000 \
  --region us-east-2
```

**Note:** Local testing uses `sam local invoke` which simulates the Lambda Function URL event structure. For continuous local testing, use the deployed Function URL with the load test script.

### Manual Testing (After Deployment)

Once deployed to AWS, test the Function URL endpoint.

**Quick single request:**

```bash
# Send a test request with default message
just test-remote

# Send a test request with custom message
just test-remote "Hello from my terminal"
```

**Quick load test:**

```bash
# Run 10 requests (automatically installs dependencies with uvx if available)
just load-test

# Run 50 requests with 5 concurrent connections
just load-test 50 5

# Run 100 requests with 10 concurrent, 100ms delay between requests
just load-test 100 10 100

# Or run directly with uvx (no installation needed!)
FUNCTION_URL=$(aws cloudformation describe-stacks \
  --stack-name boto3-keep-alive \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text)

uvx --script scripts/load-test.py $FUNCTION_URL -n 100 -c 10 -d 100 -o results.json

# Or with pip install (if uvx not available)
pip install requests
python3 scripts/load-test.py $FUNCTION_URL -n 100 -c 10 -d 100 -o results.json
```

**Load test options:**
- `-n, --num-requests`: Number of requests to send (default: 10)
- `-c, --concurrency`: Number of concurrent workers (default: 1)
- `-d, --delay`: Delay in milliseconds between requests (default: 0)
- `-u, --user-prefix`: User ID prefix (default: loadtest)
- `-o, --output`: Save results to JSON file

**Load test behavior:**
The load test simulates realistic user traffic patterns:
- Uses a queue to dynamically distribute requests across workers
- Worker 0 sends requests as fast as possible (no delay) - simulates a "power user"
- Other workers apply the specified delay between their requests - simulates normal users with "think time"
- All requests complete as quickly as possible since worker 0 isn't throttled
- Example: `-c 5 -d 1000` creates 5 workers where worker 0 fires rapidly and workers 1-4 wait 1 second between requests

**Manual curl test:**

**1. Test successful post creation:**

```bash
# Replace with your actual Function URL
FUNCTION_URL="https://your-function-url.lambda-url.us-east-1.on.aws/"

curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "message": "Hello from SAM!"}'
```

**Expected response:**
```json
{
  "postId": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Post created successfully"
}
```

**2. Test error handling (missing user_id):**

```bash
curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{"message": "Missing user_id"}'
```

**Expected response:**
```json
{
  "error": "Missing required field: user_id"
}
```

**3. Test error handling (missing message):**

```bash
curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'
├── src/
│   └── handler.py                # Lambda function handler
```
│   ├── load-test.py              # Load testing script with realistic traffic patterns
│   └── start-dynamodb-local.sh   # Script to start DynamoDB Local with table setup
├── template.yaml                 # SAM template (Infrastructure as Code)
├── iam-policy.json              # Least-privilege IAM policy for deployment
├── Justfile                      # Automation commands
├── pyproject.toml               # Python project configuration and dependencies
├── events/                       # Sample events for local testing
│   ├── sample-post.json         # Valid POST request
│   └── invalid-post.json        # Invalid request (missing user_id)
├── samconfig.toml               # SAM CLI configuration (auto-generated)
└── README.md                    # This file
```bash

### Minimal Deployment Package

The project uses a `src/` directory structure to ensure only necessary files are included in the Lambda deployment package:

- **Source code**: Only `src/handler.py` and its dependencies are packaged
- **No development files**: README, Justfile, tests, scripts, etc. are automatically excluded
- **Smaller package size**: Reduces cold start times and deployment duration
- **Faster uploads**: Less data to transfer to AWS

By using `CodeUri: src` in the SAM template, only the contents of the `src/` directory are included in the deployment package.
aws dynamodb scan --table-name keepalive-test
```

## Monitoring and Logs

### View CloudWatch Logs

**Tail logs in real-time:**

```bash
# View all logs
- `just check` - Run all checks (lint, format check, typecheck)
- `just fix` - Run linter with auto-fix and format code
just logs
- `just build` - Build with uv-generated requirements.txt
- `just deploy` - Deploy to AWS (uses saved config)
- `just deploy-guided` - Deploy with guided setup (first time)
- `just ship` - Build and deploy in one command

- `just test-remote [-m MESSAGE]` - Send a test request to deployed function
- `just load-test [-n NUM] [-c CONCURRENCY] [-d DELAY]` - Run load test
```
- `just logs [--filter FILTER]` - Tail CloudWatch logs
This streams CloudWatch logs from the Lambda function, showing all invocations, errors, and debug information.
- `just dynamodb-local` - Start DynamoDB Local
**View logs in AWS Console:**
1. Navigate to CloudWatch → Log Groups
2. Find `/aws/lambda/boto3-keep-alive-PostsFunction`
3. Click on the latest log stream

### CloudWatch Insights Queries

Use CloudWatch Insights for structured log analysis:

```sql
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 20
```

## Cleanup

To delete all AWS resources created by this application:

```bash
just destroy
```

This removes:
- Lambda function
- DynamoDB table
- IAM roles and policies
- CloudWatch log groups
- CloudFormation stack

**Note:** This operation is irreversible. All data in the DynamoDB table will be permanently deleted.

## Project Structure

```
.
├── src/
│   └── handler.py                # Lambda function handler
├── scripts/
│   ├── load-test.py              # Load testing script with realistic traffic patterns
│   └── start-dynamodb-local.sh   # Script to start DynamoDB Local with table setup
├── template.yaml                 # SAM template (Infrastructure as Code)
├── iam-policy.json              # Least-privilege IAM policy for deployment
├── Justfile                      # Automation commands
├── pyproject.toml               # Python project configuration and dependencies
├── events/                       # Sample events for local testing
│   ├── sample-post.json         # Valid POST request
│   └── invalid-post.json        # Invalid request (missing user_id)
├── samconfig.toml               # SAM CLI configuration (auto-generated)
└── README.md                    # This file
```

### Minimal Deployment Package

The project uses a `src/` directory structure to ensure only necessary files are included in the Lambda deployment package:

- **Source code**: Only `src/handler.py` and its dependencies are packaged
- **No development files**: README, Justfile, tests, scripts, etc. are automatically excluded
- **Smaller package size**: Reduces cold start times and deployment duration
- **Faster uploads**: Less data to transfer to AWS

By using `CodeUri: src` in the SAM template, only the contents of the `src/` directory are included in the deployment package.

## Available Commands

Run `just` to see all available commands:

```bash
just
```

**Common commands:**

- `just check` - Run all checks (lint, format check, typecheck)
- `just fix` - Run linter with auto-fix and format code
- `just validate` - Validate SAM template syntax
- `just build` - Build with uv-generated requirements.txt
- `just deploy` - Deploy to AWS (uses saved config)
- `just deploy-guided` - Deploy with guided setup (first time)
- `just ship` - Build and deploy in one command
- `just info` - Show stack status and outputs
- `just test-remote [-m MESSAGE]` - Send a test request to deployed function
- `just load-test [-n NUM] [-c CONCURRENCY] [-d DELAY]` - Run load test
- `just test-local` - Test function locally with sample event
- `just logs [--filter FILTER]` - Tail CloudWatch logs
- `just destroy` - Delete all AWS resources
- `just dynamodb-local` - Start DynamoDB Local
- `just dynamodb-local-stop` - Stop DynamoDB Local

## Configuration

### Environment Variables

The Lambda function uses the following configuration:

- **Runtime**: Python 3.14
- **Architecture**: ARM64 (AWS Graviton2)
- **Memory**: 256 MB
- **Timeout**: 30 seconds
- **DynamoDB Table**: `keepalive-test`

### Performance Benefits of ARM64

ARM64 Lambda functions on AWS Graviton2 provide:
- **Up to 34% better price-performance** compared to x86_64
- **19% faster execution** for Python workloads
- **Lower cold start times** in many scenarios
- **Better energy efficiency**

### Customization

To customize the deployment:

1. Edit `template.yaml` to modify resources
2. Update the `Environment` parameter (dev, staging, prod)
3. Change architecture (arm64 ↔ x86_64) in the `Architectures` section
3. Modify table name or Lambda configuration as needed
4. Run `just validate` to check changes
5. Run `just deploy` to apply updates

## Troubleshooting

### Permission Errors During Deployment

If you see errors like:
```
User: arn:aws:iam::ACCOUNT:user/USERNAME is not authorized to perform: iam:CreateRole
```

This means the IAM policy hasn't been attached to your user yet. Follow these steps:

```bash
# 1. Get your account ID and username
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
YOUR_USERNAME=$(aws sts get-caller-identity --query 'Arn' --output text | cut -d'/' -f2)

# 2. Create the policy (if it doesn't exist)
aws iam create-policy \
  --policy-name Boto3KeepAliveDeployPolicy \
  --policy-document file://iam-policy.json 2>/dev/null || echo "Policy already exists"

# 3. Attach the policy to your user
aws iam attach-user-policy \
  --user-name $YOUR_USERNAME \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/Boto3KeepAliveDeployPolicy

# 4. Verify it's attached
aws iam list-attached-user-policies --user-name $YOUR_USERNAME

# 5. Try deploying again
just deploy
```

### Build Failures

If `just build` fails:

```bash
# Check SAM CLI version
sam --version

# Validate template
just validate

# Check Python version
python3 --version
```

### Deployment Failures

If `just deploy` fails:

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name boto3-keep-alive \
  --max-items 10
```

### Function Errors

If the Lambda function returns errors:

```bash
# View recent logs
just logs

# Check DynamoDB table exists
aws dynamodb describe-table --table-name keepalive-test

# Test locally first
just test-local
```

### Permission Errors

If you encounter IAM permission errors:

- Ensure your AWS credentials have the required permissions (see `iam-policy.json`)
- Apply the least-privilege IAM policy provided in the repository
- Check the CloudFormation stack events for specific permission issues
- Verify your AWS account has sufficient service quotas
- For CI/CD pipelines, ensure the service role has the necessary permissions

## Benefits of SAM

This project uses AWS SAM for:

- **Native AWS Integration**: Built and maintained by AWS
- **Simpler Configuration**: YAML-based templates without plugins
- **Superior Local Testing**: Excellent local development with `sam local`
- **No Third-Party Dependencies**: No npm packages required
- **CloudFormation Foundation**: Direct mapping to CloudFormation
- **Active Development**: Regular updates for new Lambda features

## License

This is an example project for demonstration purposes.
