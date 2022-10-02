"""Lambda function to handle a post and persist to DynamoDB."""
import json
from time import perf_counter
from uuid import uuid4

import boto3
import botocore
from botocore.config import Config


BOTO_VERSION = boto3.__version__
BOTOCORE_VERSION = botocore.__version__

TABLE_NAME = "keepalive-test"

client = boto3.client("dynamodb", config=Config(tcp_keepalive=True))


def lambda_handler(event, _context):
    body = json.loads(event["body"])

    user_id, message = body["user_id"], body["message"]
    post_id = str(uuid4())

    start = perf_counter()

    client.put_item(
        TableName=TABLE_NAME,
        Item={
            "userId": {"S": user_id},
            "postId": {"S": post_id},
            "message": {"S": message},
        },
    )

    end = perf_counter()
    duration_in_ms = (end - start) * 1000
    print(f"DynamoDb.put_item[ms]: {duration_in_ms}")

    return {
        "statusCode": 200,
        "body": {
            "post_id": post_id,
            "boto3_version": BOTO_VERSION,
            "botocore_version": BOTOCORE_VERSION,
            "duration_in_ms": duration_in_ms,
        },
    }
