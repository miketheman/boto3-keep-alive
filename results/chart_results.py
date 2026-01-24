#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "matplotlib",
#     "pandas",
# ]
# ///

import matplotlib.pyplot as plt
import pandas as pd

TESTS = ["no-keepalive", "inline-keepalive", "envvar-keepalive"]


def process_data(test_name):
    # Read data, skipping columns we don't care about
    df = pd.read_csv(
        f"{test_name}.txt",
        sep=" ",
        header=None,
        names=["Timestamp", "Operation", "Latency"],
    )

    # The 'Operation' column actually contains the string "DynamoDb.put_item[ms]:"
    # which might need cleaning but isn't critical if we just ignore it.
    # The numeric latency is in the 4th column, which we named 'Latency'.

    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df["Latency"] = pd.to_numeric(df["Latency"])

    # Calculate time differences to spot gaps
    df["TimeDiff"] = df["Timestamp"].diff().dt.total_seconds()

    # # Summary statistics
    # print("Summary Statistics:")
    # print(df['Latency'].describe())

    # Visualize to see patterns
    plt.figure(figsize=(10, 5))
    plt.plot(df["Timestamp"], df["Latency"], marker="o")
    plt.title("Latency over Time")
    plt.xlabel("Time")
    plt.ylabel("Latency (ms)")
    plt.grid(True)
    plt.savefig(f"{test_name}-latency_over_time.png")

    # Visualize distribution
    plt.figure(figsize=(10, 5))
    plt.hist(df["Latency"], bins=20, edgecolor="black")
    plt.title("Latency Distribution")
    plt.xlabel("Latency (ms)")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.savefig(f"{test_name}-latency_hist.png")


if __name__ == "__main__":
    for test_name in TESTS:
        process_data(test_name)
