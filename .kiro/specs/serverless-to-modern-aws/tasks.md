# Implementation Plan: Serverless Framework to Modern AWS Migration

## Overview

This implementation plan transforms a Serverless Framework Lambda project to use AWS SAM. The approach focuses on infrastructure modernization while keeping handler.py unchanged. Tasks are organized to build incrementally, with each step validated before moving forward.

## Tasks

- [x] 1. Create SAM template with Lambda function and DynamoDB table
  - Create `template.yaml` in project root
  - Define AWS::Serverless::Function resource for Lambda
  - Configure Function URL with AuthType: NONE
  - Define AWS::DynamoDB::Table resource with post_id as primary key
  - Ensure table name matches the hardcoded name in handler.py
  - Set BillingMode to PAY_PER_REQUEST for on-demand billing
  - Add DynamoDBWritePolicy to Lambda function for table access
  - Set Python 3.14 runtime in Globals section
  - Add resource tags (Application, ManagedBy, Environment)
  - Define outputs for FunctionUrl and TableName
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 4.1, 4.4, 4.5, 7.1, 7.2, 10.1, 10.2, 10.3, 10.4, 11.1, 11.2, 11.3, 11.4_

- [x] 2. Create Justfile for automation commands
  - Create `Justfile` in project root
  - Add `default` recipe to list all available commands
  - Add `validate` recipe to run `sam validate --lint`
  - Add `build` recipe to run `sam build`
  - Add `deploy` recipe that runs build then `sam deploy --guided`
  - Add `deploy-quick` recipe for fast deployment with saved config
  - Add `test-local` recipe to invoke function locally with sample event
  - Add `start-local` recipe to start local API with `sam local start-api`
  - Add `logs` recipe to tail CloudWatch logs
  - Add `destroy` recipe to run `sam delete --no-prompts`
  - Add `dynamodb-local` recipe to run DynamoDB Local in Docker (optional)
  - _Requirements: 8.1, 8.2, 8.3, 8.5, 6.5_

- [x] 3. Create sample event files for local testing
  - Create `events/` directory
  - Create `events/sample-post.json` with valid POST request event
  - Include Lambda Function URL event structure (version 2.0)
  - Include body with valid user_id and message
  - Create `events/invalid-post.json` with missing user_id for error testing
  - _Requirements: 6.3_

- [x] 4. Update README with SAM deployment instructions
  - Update README.md with SAM-specific setup instructions
  - Document prerequisites (AWS CLI, SAM CLI, Just)
  - Add deployment section with `just deploy` command
  - Add local testing section with `just test-local` and `just start-local`
  - Add manual testing section with curl examples
  - Add cleanup section with `just destroy` command
  - Document how to view logs with `just logs`
  - Include Function URL testing examples
  - _Requirements: 9.4_

- [x] 5. Verify handler.py compatibility
  - Confirm handler.py uses hardcoded table name that matches SAM template
  - Verify handler.py imports boto3 without bundling it
  - Ensure handler.py is compatible with Python 3.14 syntax
  - Confirm handler.py stays in root directory (no move needed)
  - Verify no sensitive credentials are hardcoded
  - _Requirements: 2.2, 2.4, 2.5, 7.2, 7.3, 12.1, 12.2, 12.3, 12.4_

- [x] 6. Checkpoint - Validate and test locally
  - Run `just validate` to check SAM template syntax
  - Run `just build` to build the Lambda package
  - Run `just test-local` to test with sample event
  - Verify local invocation works correctly
  - Check that no boto3 is bundled in .aws-sam/build
  - _Requirements: 6.1, 6.4_

- [x] 7. Deploy to AWS and verify
  - Run `just deploy` to deploy stack to AWS
  - Note the Function URL from CloudFormation outputs
  - Test Function URL with curl (successful post creation)
  - Test Function URL with curl (error handling for missing fields)
  - Verify DynamoDB table created with correct schema
  - Check DynamoDB for created records using AWS CLI
  - Verify CloudWatch logs with `just logs`
  - Confirm all resources have proper tags
  - _Requirements: 1.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 5.5, 12.5_

- [x] 8. Test cleanup process
  - Run `just destroy` to delete all resources
  - Verify CloudFormation stack is deleted
  - Confirm DynamoDB table is removed
  - Confirm Lambda function is removed
  - Verify no orphaned resources remain
  - _Requirements: 8.4_

## Notes

- Handler.py code remains completely unchanged throughout this process
- All changes are infrastructure-only (SAM template, Justfile, documentation)
- Testing is manual using curl after deployment
- Each checkpoint ensures incremental validation before proceeding
- The project structure stays minimal with handler.py in root directory
