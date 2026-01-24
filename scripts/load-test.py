#!/usr/bin/env -S uv run --script
"""
Load testing script for boto3-keep-alive Lambda function.

Sends POST requests to the Lambda Function URL to simulate traffic
and generate logs for analysis.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.32.5",
# ]
# ///
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from queue import Queue
from typing import Any

import requests


def send_request(
    url: str, user_id: str, message: str, request_num: int
) -> dict[str, Any]:
    """Send a single POST request to the Lambda function."""
    start_time = time.time()

    payload = {
        "user_id": user_id,
        "message": message,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        duration = (time.time() - start_time) * 1000  # Convert to ms

        result = {
            "request_num": request_num,
            "status_code": response.status_code,
            "duration_ms": duration,
            "success": response.status_code == 200,
            "response": None,
            "error": None,
        }

        if response.status_code == 200:
            try:
                result["response"] = response.json()
            except ValueError as e:
                result["success"] = False
                result["error"] = f"Invalid JSON response: {e}"

        return result
    except requests.exceptions.RequestException as e:
        duration = (time.time() - start_time) * 1000
        return {
            "request_num": request_num,
            "status_code": None,
            "duration_ms": duration,
            "success": False,
            "response": None,
            "error": str(e),
        }


def worker_task(
    worker_id: int,
    url: str,
    request_queue: Queue,
    delay_ms: int,
    user_prefix: str,
) -> list[dict]:
    """Execute requests from queue serially for a single worker with delays."""
    results = []
    request_count = 0

    while True:
        try:
            request_num = request_queue.get_nowait()
        except Exception:
            # Queue is empty, worker is done
            break

        request_count += 1
        user_id = f"{user_prefix}-{request_num % 10}"
        message = (
            f"Load test message {request_num} from worker {worker_id} "
            f"at {datetime.now().isoformat()}"
        )

        result = send_request(url, user_id, message, request_num)
        results.append(result)

        # Print progress
        status = "✓" if result["success"] else "✗"
        print(
            f"{status} Worker {worker_id} - Request {request_count} "
            f"(#{result['request_num']}) - {result['status_code']} - "
            f"{result['duration_ms']:.2f}ms"
        )

        # Add delay between requests (except after the last one)
        # Worker 0 never delays (sends as fast as possible)
        if worker_id > 0 and delay_ms > 0 and not request_queue.empty():
            time.sleep(delay_ms / 1000.0)

    return results


def run_load_test(
    url: str,
    num_requests: int,
    concurrency: int,
    delay_ms: int,
    user_prefix: str,
) -> list[dict]:
    """Run load test with specified parameters.

    Uses a queue to distribute requests across workers dynamically.
    Worker 0 sends as fast as possible, other workers apply delays.
    """
    print("Starting load test:")
    print(f"  URL: {url}")
    print(f"  Total requests: {num_requests}")
    print(f"  Concurrent workers: {concurrency}")
    print(f"  Delay between requests: {delay_ms}ms")
    print(f"  User prefix: {user_prefix}")
    if concurrency > 1:
        print(
            f"  Pattern: Worker 0 sends without delay, other workers delay "
            f"{delay_ms}ms between requests"
        )
    else:
        print("  Pattern: Single worker sends without delay")
    print()

    # Create queue and populate with request numbers
    request_queue = Queue()
    for i in range(num_requests):
        request_queue.put(i + 1)

    results = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []

        for worker_id in range(concurrency):
            future = executor.submit(
                worker_task,
                worker_id,
                url,
                request_queue,
                delay_ms,
                user_prefix,
            )
            futures.append(future)

        # Collect results from all workers
        for future in as_completed(futures):
            worker_results = future.result()
            results.extend(worker_results)

    # Sort results by request number for consistent output
    results.sort(key=lambda x: x["request_num"])

    return results


def print_summary(results: list[dict]):
    """Print summary statistics."""
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful

    durations = [r["duration_ms"] for r in results if r["success"]]

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total requests:     {total}")
    print(f"Successful:         {successful} ({successful / total * 100:.1f}%)")
    print(f"Failed:             {failed} ({failed / total * 100:.1f}%)")

    if durations:
        print("\nResponse times (ms):")
        print(f"  Min:              {min(durations):.2f}")
        print(f"  Max:              {max(durations):.2f}")
        print(f"  Average:          {sum(durations) / len(durations):.2f}")
        print(f"  Median:           {sorted(durations)[len(durations) // 2]:.2f}")

    # Show errors if any
    errors = [r for r in results if not r["success"]]
    if errors:
        print("\nErrors:")
        error_types = {}
        for error in errors:
            error_msg = error.get("error") or f"HTTP {error.get('status_code')}"
            error_types[error_msg] = error_types.get(error_msg, 0) + 1

        for error_msg, count in error_types.items():
            print(f"  {error_msg}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Load test the boto3-keep-alive Lambda function"
    )
    parser.add_argument(
        "url",
        help="Lambda Function URL endpoint",
    )
    parser.add_argument(
        "-n",
        "--num-requests",
        type=int,
        default=10,
        help="Number of requests to send (default: 10)",
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=1,
        help="Number of concurrent requests (default: 1)",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=int,
        default=0,
        help="Delay in milliseconds between requests (default: 0)",
    )
    parser.add_argument(
        "-u",
        "--user-prefix",
        default="loadtest",
        help="User ID prefix (default: loadtest)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Save results to JSON file",
    )

    args = parser.parse_args()

    # Validate URL
    if not args.url.startswith("http"):
        print("Error: URL must start with http:// or https://")
        sys.exit(1)

    # Run load test
    start_time = time.time()
    results = run_load_test(
        args.url,
        args.num_requests,
        args.concurrency,
        args.delay,
        args.user_prefix,
    )
    total_time = time.time() - start_time

    # Print summary
    print_summary(results)
    print(f"\nTotal time:         {total_time:.2f}s")
    print(f"Requests/second:    {len(results) / total_time:.2f}")

    # Save results if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "config": {
                        "url": args.url,
                        "num_requests": args.num_requests,
                        "concurrency": args.concurrency,
                        "delay_ms": args.delay,
                        "user_prefix": args.user_prefix,
                    },
                    "results": results,
                    "total_time_seconds": total_time,
                },
                f,
                indent=2,
            )
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
