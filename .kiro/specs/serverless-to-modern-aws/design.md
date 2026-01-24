# Design Document: Serverless Framework to Modern AWS Migration

## Overview

This design document outlines the modernization of a legacy Serverless Framework Lambda project to use AWS SAM (Serverless Application Model). The migration focuses on infrastructure modernization while preserving the existing handler logic. The project will transition from Serverless Framework to AWS SAM, update to Python 3.14 runtime, implement proper Infrastructure as Code with DynamoDB table definitions, add Justfile automation for common operations, minimize external dependencies by leveraging AWS Lambda's managed runtime, and implement comprehensive resource tagging for easy identification and cleanup.

The core principle of this modernization is **infrastructure-only changes** - the handler.py business logic remains unchanged, ensuring zero risk to the application's functionality while gaining all the benefits of modern AWS tooling.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   HTTP Client   │
└────────┬────────┘
         │ POST request
         │ (user_id, message)
         ▼
┌─────────────────────────┐
│  Lambda Function URL    │
│  (Public HTTPS endpoint)│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Lambda Function       │
│   (Python 3.14)         │
│   - handler.py          │
│   - Validates input     │
│   - Generates post_id   │
│   - Writes to DynamoDB  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   DynamoDB Table        │
│   - PK: post_id         │
│   - Attributes:         │
│     * user_id           │
│     * message           │
│     * timestamp         │
└─────────────────────────┘
```

### Infrastructure as Code: SAM vs Serverless Framework

**Why AWS SAM over Serverless Framework:**

1. **Native AWS Integration**: SAM is built and maintained by AWS, ensuring first-class support for all AWS services and features
2. **Simpler Configuration**: YAML-based templates are more straightforward than Serverless Framework's plugin ecosystem
3. **Superior Local Testing**: `sam local` provides excellent local development experience with DynamoDB Local integration
4. **No Third-Party Dependencies**: Eliminates the need for Serverless Framework npm packages and plugins
5. **CloudFormation Foundation**: Direct mapping to CloudFormation provides transparency and predictability
6. **Active Development**: SAM is actively developed by AWS with regular updates for new Lambda features
7. **Industry Standard**: SAM has become the de facto standard for serverless applications on AWS

### Deployment Workflow

```
Developer
    │
    ├─> just validate     (Validates SAM template)
    ├─> just build        (Builds Lambda package)
    ├─> just deploy       (Deploys to AWS)
    ├─> just test-local   (Tests locally with SAM CLI)
    ├─> just logs         (Tails CloudWatch logs)
    └─> just destroy      (Cleans up all resources)
```

## Components and Interfaces

### 1. SAM Template (template.yaml)

The SAM template defines all infrastructure resources using CloudFormation syntax with SAM transforms.

**Key Sections:**

- **Globals**: Shared configuration for all functions (runtime, timeout, memory)
- **Parameters**: Configurable values (environment name, table name)
- **Resources**:
  - Lambda Function with Function URL
  - DynamoDB Table
  - IAM Role with least-privilege policies
- **Outputs**: Function URL, Table Name, Function ARN

**Template Structure:**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]

Globals:
  Function:
    Runtime: python3.14
    Timeout: 30
    MemorySize: 256
    Tags:
      Application: serverless-modernization
      ManagedBy: SAM

Resources:
  PostsFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      CodeUri: .
      FunctionUrlConfig:
        AuthType: NONE
      Policies:
        - DynamoDBWritePolicy:
            TableName: !Ref PostsTable

  PostsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      AttributeDefinitions:
        - AttributeName: post_id
          AttributeType: S
      KeySchema:
        - AttributeName: post_id
          KeyType: HASH
      BillingMode: PAY_PER_REQUEST
      Tags:
        - Key: Application
          Value: serverless-modernization
        - Key: ManagedBy
          Value: SAM

Outputs:
  FunctionUrl:
    Description: Lambda Function URL
    Value: !GetAtt PostsFunctionUrl.FunctionUrl
  TableName:
    Description: DynamoDB Table Name
    Value: !Ref PostsTable
```

### 2. Lambda Handler (handler.py)

The handler code **remains unchanged** from the original Serverless Framework implementation and stays in the root directory. It continues to:

- Accept POST requests via Lambda Function URL
- Extract `user_id` and `message` from the request body
- Generate a unique `post_id` using UUID
- Write the record to DynamoDB (using hardcoded table name)
- Return appropriate HTTP responses

**Handler Interface:**
```python
def lambda_handler(event, context):
    """
    Lambda handler for POST requests.
    
    Args:
        event: Lambda event containing HTTP request data
        context: Lambda context object
        
    Returns:
        dict: HTTP response with statusCode, headers, and body
    """
```

**Configuration:**
- Table name is hardcoded in handler.py (e.g., 'posts-dev')
- Must match the table name defined in SAM template

**Dependencies:**
- `boto3`: AWS SDK (provided by Lambda managed runtime)
- `json`: Standard library
- `uuid`: Standard library
- `datetime`: Standard library

### 3. Justfile Automation

The Justfile provides convenient commands for all common operations, abstracting away the complexity of SAM CLI commands.

**Commands:**

```justfile
# Default recipe lists all available commands
default:
    @just --list

# Validate SAM template syntax
validate:
    sam validate --lint

# Build the Lambda function
build:
    sam build

# Deploy to AWS
deploy: build
    sam deploy --guided

# Quick deploy (uses saved config)
deploy-quick: build
    sam deploy

# Test function locally with sample event
test-local: build
    sam local invoke PostsFunction --event events/sample-post.json

# Start local API for testing
start-local: build
    sam local start-api

# Tail CloudWatch logs
logs:
    sam logs --name PostsFunction --tail

# Delete all resources
destroy:
    sam delete --no-prompts

# Run local DynamoDB (requires Docker)
dynamodb-local:
    docker run -p 8000:8000 amazon/dynamodb-local
```

### 4. Project Structure

The project maintains the existing directory structure with minimal changes - only adding SAM-specific files:

```
project-root/
├── template.yaml           # SAM template (IaC) - NEW
├── Justfile               # Automation commands - NEW
├── samconfig.toml         # SAM CLI configuration (auto-generated) - NEW
├── README.md              # Updated documentation
├── handler.py             # Lambda handler (UNCHANGED - stays in root)
└── events/                # NEW - Sample events for testing
    ├── sample-post.json   
    └── invalid-post.json  
```

**Key Points:**
- `handler.py` stays in the root directory (no src/ folder needed)
- SAM template references `handler.py` directly with `CodeUri: .`
- Minimal disruption to existing structure
- No tests/ directory needed (manual testing only)

## Data Models

### DynamoDB Table Schema

**Table Name**: `posts-{environment}` (e.g., `posts-dev`)

**Primary Key**:
- Partition Key: `post_id` (String)

**Attributes**:
- `post_id` (String): Unique identifier (UUID v4)
- `user_id` (String): User identifier from request
- `message` (String): Post message content
- `timestamp` (String): ISO 8601 timestamp of creation

**Billing Mode**: PAY_PER_REQUEST (on-demand)
- No capacity planning required
- Automatically scales with traffic
- Cost-effective for variable workloads

**Example Item**:
```json
{
  "post_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "message": "Hello, world!",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Lambda Event Structure

**Input Event** (Lambda Function URL):
```json
{
  "version": "2.0",
  "routeKey": "$default",
  "rawPath": "/",
  "requestContext": {
    "http": {
      "method": "POST",
      "path": "/",
      "protocol": "HTTP/1.1"
    }
  },
  "body": "{\"user_id\": \"user123\", \"message\": \"Hello, world!\"}",
  "isBase64Encoded": false
}
```

**Success Response**:
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"post_id\": \"550e8400-e29b-41d4-a716-446655440000\", \"message\": \"Post created successfully\"}"
}
```

**Error Response**:
```json
{
  "statusCode": 400,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"error\": \"Missing required field: user_id\"}"
}
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system - essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Input Validation Consistency

*For any* POST request, if the request body is missing required fields (user_id or message) or contains invalid data types, the handler should return a 400 error response with a descriptive error message, and if the request contains valid user_id and message fields, the handler should proceed with processing.

**Validates: Requirements 3.1, 3.5**

### Property 2: Post ID Uniqueness

*For any* sequence of valid POST requests, each generated post_id should be unique across all invocations, ensuring no collisions in the DynamoDB table.

**Validates: Requirements 3.2**

### Property 3: Complete DynamoDB Write

*For any* valid POST request with user_id and message, when the handler generates a post_id, the resulting DynamoDB write operation should include all required fields: post_id (as primary key), user_id, message, and timestamp.

**Validates: Requirements 3.3, 4.2**

### Property 4: Response Format Consistency

*For any* POST request, the handler response should maintain the same format as the original Serverless Framework implementation: for successful requests, a 200 status code with JSON body containing post_id and success message; for failed requests, an appropriate error status code (400, 500) with JSON body containing an error message.

**Validates: Requirements 3.4, 12.5**

### Property 5: Exception Handling Safety

*For any* exception raised during request processing (including DynamoDB errors, JSON parsing errors, or unexpected runtime errors), the handler should catch the exception, log it with context information, and return an appropriate HTTP error response (500 status code) rather than allowing the exception to propagate uncaught.

**Validates: Requirements 5.2**

### Property 6: Structured Logging Completeness

*For any* request processed by the handler, the logs should include structured entries (JSON format) for: incoming request metadata, input validation results, DynamoDB operation attempts, and any errors encountered, ensuring all logs are compatible with CloudWatch Insights queries.

**Validates: Requirements 5.1, 5.3, 5.4, 5.5**

**Note:** These properties are documented for specification purposes. Testing will focus on unit tests with specific examples rather than property-based testing.

## Error Handling

### Error Categories

**1. Input Validation Errors (400 Bad Request)**
- Missing required fields (user_id or message)
- Invalid JSON in request body
- Empty or null values for required fields
- Invalid data types

**Error Response Format:**
```json
{
  "statusCode": 400,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"error\": \"Missing required field: user_id\"}"
}
```

**2. DynamoDB Errors (500 Internal Server Error)**
- Table not found
- Insufficient permissions
- Throttling errors
- Network connectivity issues

**Error Response Format:**
```json
{
  "statusCode": 500,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"error\": \"Failed to write to database\"}"
}
```

**3. Unexpected Runtime Errors (500 Internal Server Error)**
- Unhandled exceptions
- Runtime errors
- Memory or timeout issues

**Error Response Format:**
```json
{
  "statusCode": 500,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"error\": \"Internal server error\"}"
}
```

### Error Handling Strategy

**Logging:**
- All errors are logged with full context (request ID, input data, stack trace)
- Structured logging format for CloudWatch Insights
- Error severity levels: ERROR for 500s, WARN for 400s

**User-Facing Messages:**
- Generic error messages for 500 errors (no internal details exposed)
- Specific validation messages for 400 errors (help users fix input)
- No sensitive information in error responses

**Retry Strategy:**
- No automatic retries in handler (client responsibility)
- DynamoDB SDK handles transient errors automatically
- Idempotent operations allow safe client retries

## Testing Strategy

### Manual Testing Approach

Since the handler.py code remains unchanged from the original implementation, we'll rely on manual testing to verify that the infrastructure changes work correctly. This is the most practical approach for a simple Lambda function.

**Testing Method:**
- Deploy to AWS using SAM
- Test the Function URL endpoint using curl
- Verify DynamoDB records are created
- Check CloudWatch logs for errors

**No automated unit tests are required** - manual verification is sufficient for this modernization.

### Local Testing

**SAM CLI Local Testing:**

```bash
# Test with sample event
just test-local

# Start local API endpoint
just start-local

# Test with curl
curl -X POST http://localhost:3000/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "message": "Hello, world!"}'
```

**Local DynamoDB (Optional):**

```bash
# Start DynamoDB Local in Docker
just dynamodb-local

# Configure handler to use local endpoint
export AWS_ENDPOINT_URL=http://localhost:8000
```

### Manual Testing After Deployment

### Manual Testing After Deployment

Verify the complete deployment with manual testing:

```bash
# 1. Deploy to AWS
just deploy

# 2. Get Function URL from outputs
FUNCTION_URL=$(aws cloudformation describe-stacks \
  --stack-name serverless-modernization \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text)

# 3. Test successful post creation
curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "message": "Hello from SAM!"}'

# Expected response:
# {"post_id": "...", "message": "Post created successfully"}

# 4. Test error handling (missing user_id)
curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{"message": "Missing user_id"}'

# Expected response:
# {"error": "Missing required field: user_id"}

# 5. Verify DynamoDB record
aws dynamodb scan --table-name posts-dev

# 6. Check CloudWatch logs
just logs

# 7. Clean up when done
just destroy
```

## Deployment Guide

### Prerequisites

- AWS CLI configured with appropriate credentials
- SAM CLI installed (`pip install aws-sam-cli`)
- Just command runner installed
- Docker (for local testing)

### First-Time Deployment

```bash
# 1. Validate template
just validate

# 2. Build application
just build

# 3. Deploy with guided setup (first time only)
just deploy

# Follow prompts:
# - Stack name: serverless-modernization
# - AWS Region: us-east-1 (or your preferred region)
# - Confirm changes: Y
# - Allow SAM CLI IAM role creation: Y
# - Save arguments to config: Y
```

### Subsequent Deployments

```bash
# Quick deploy using saved configuration
just deploy-quick
```

### Cleanup

```bash
# Delete all AWS resources
just destroy
```

### Monitoring

```bash
# Tail CloudWatch logs in real-time
just logs

# View logs in AWS Console
# Navigate to CloudWatch > Log Groups > /aws/lambda/serverless-modernization-PostsFunction
```

## Benefits of Modernization

### Immediate Benefits

1. **Simpler Tooling**: Native AWS tools, no third-party framework
2. **Better Local Testing**: SAM CLI provides excellent local development experience
3. **Clearer Infrastructure**: YAML templates are more transparent than Serverless Framework
4. **Easier Cleanup**: `just destroy` removes all resources cleanly
5. **Resource Tagging**: All resources properly tagged for identification

### Long-Term Benefits

1. **Maintainability**: Standard AWS tooling reduces learning curve
2. **Flexibility**: Easy to extend with additional AWS services
3. **Cost Visibility**: Better resource tagging enables cost tracking
4. **Security**: Explicit IAM policies with least privilege
5. **Scalability**: On-demand DynamoDB billing scales automatically

### No Breaking Changes

- Handler logic remains unchanged
- API interface stays the same
- Response format is identical
- DynamoDB schema unchanged
- Existing directory structure preserved (handler.py stays in root)
