"""Lambda function to handle a post and persist to DynamoDB."""

import json
import platform
import socket
import sys
from time import perf_counter
from uuid import uuid4

import boto3
import botocore

BOTO_VERSION = boto3.__version__
BOTOCORE_VERSION = botocore.__version__
PYTHON_VERSION = (
    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
)
ARCHITECTURE = platform.machine()
OS_SYSTEM = platform.system()
OS_RELEASE = platform.release()
OS_VERSION = platform.version()

TABLE_NAME = "keepalive-test"

client = boto3.client("dynamodb")


def get_socket_keepalive_status(client):
    """
    Get SO_KEEPALIVE status from the actual socket after making a request.
    Returns True/False/None (None if unable to inspect).
    """
    try:
        # Navigate: client -> endpoint -> http_session -> pool_manager -> pools
        http_session = client._endpoint.http_session
        pool_manager = http_session._manager or http_session._pool_manager
        pools_dict = pool_manager.pools._container

        # Check the first available connection in any pool
        for pool in pools_dict.values():
            if pool.pool and pool.pool.qsize() > 0:
                conn = pool.pool.get(block=False)
                if conn and conn.sock:
                    keepalive = conn.sock.getsockopt(
                        socket.SOL_SOCKET, socket.SO_KEEPALIVE
                    )
                    pool.pool.put(conn)  # Put it back
                    return bool(keepalive)
    except Exception:
        pass
    return None


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
    duration_in_ms = round((end - start) * 1000, 5)
    print(f"DynamoDb.put_item[ms]: {duration_in_ms}")

    # Check socket keepalive status after the request
    tcp_keepalive = get_socket_keepalive_status(client)

    return {
        "statusCode": 200,
        "body": {
            "post_id": post_id,
            "boto3_version": BOTO_VERSION,
            "botocore_version": BOTOCORE_VERSION,
            "python_version": PYTHON_VERSION,
            "architecture": ARCHITECTURE,
            "os_system": OS_SYSTEM,
            "os_release": OS_RELEASE,
            "os_version": OS_VERSION,
            "tcp_keepalive": tcp_keepalive,
            "duration_in_ms": duration_in_ms,
        },
    }
