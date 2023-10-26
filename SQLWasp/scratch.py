#!/usr/bin/env python3.12
# scratch.py
from rich.console import Console
from sklearn.datasets import load_iris
import pandas as pd
import numpy as np

c = Console()
train_input_file = "data/output/assess_latency/assess_latency.csv"
df = pd.read_csv(train_input_file)
df = df.dropna()
df = df.drop(columns=["URL", "Test Passed", "Test Final Evaluation"])
# c.print(df["Test Passed"])
c.print(df.dropna())


def _create_pandaz_table(self):
    table_data = [["URL", url],
                  ["Host", host],
                  ["Number of GET Requests Sent", accuracy],
                  ["Number of Ping Requests Sent", accuracy],
                  ["Requests Delay (secs) ", delay],
                  ["Communication Quality Threshold (secs)", threshold],
                  ["Ping Threshold (secs)", ping_threshold],
                  ["Standard Deviation Threshold (secs)", std_deviation_threshold],
                  ["Ping Standard Deviation Threshold (secs)", ping_std_deviation_threshold],
                  ["GET Responses Latency Average (secs)", latency_average],
                  ["Min GET Responses Latency (secs)", min(latencies_list)],
                  ["Max GET Responses Latency (secs)", max(latencies_list)],
                  ["Ping responses Latency Average (secs)", ping_latency_average],
                  ["Min Ping responses Latency (secs)", min(ping_latencies_list)],
                  ["Max Ping responses Latency (secs)", max(ping_latencies_list)],
                  ["Standard Deviation (secs)", std_deviation],
                  ["Ping Standard Deviation (secs)", ping_std_deviation]]
    for status_code_category, response in status_codes.items():
        table_data.append(
            [
                "Status Code (n. of responses): {status_code_category}",
                len(status_codes.get(status_code_category))
            ]
        )
    table_data.append(["Test Final Evaluation", test_final_evaluation])
    table_data.append(["Test Passed", test_passed])
    a = np.array(table_data)
    c.print(a)
    return table_data


