#!/usr/bin/env python3.12
# scratch.py

import functools
import time
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console

from SQLWasp.assess_latency import AssessLatency

c = Console()

futures = []
# urls = ["https://sivanandamusic.it", "https://www.kamapuaa.it"]
#
urls = [
    "http://kamapuaa.it", "https://sivanandamusic.it/", "https://sivanandamusic.it/fango", "https://google.com", "https://www.rainews.it/",
    "https://www.ilsole24ore.com/", "https://www.padovanet.it/"
]
#
# accuracy = 1
# threshold = 0.1
# ping_threshold = 0.1
# std_deviation_threshold = 0.1
# ping_std_deviation_threshold = 0.1
# delay = 0.0
# outfile = "data/output/assess_latency/assess_latency.csv"
# verbose = True


def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.time()
        c.print(f"Start time '{func.__name__}: {start_time}'")
        value = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        c.print(f"End time '{func.__name__}: {end_time}'")
        c.print(f"Completed '{func.__name__} in: {elapsed_time}'")
        return value

    return wrapper_timer


@timer
def fire_assess_latency(urls_list, *args, **kwargs):
    with ThreadPoolExecutor(max_workers=len(urls_list)) as executor:
        for url in urls_list:
            lat_ass = AssessLatency(url, *args, **kwargs)
            future = executor.submit(
                lat_ass.run
            )
            futures.append(future)


if __name__ == '__main__':
    fire_assess_latency(
        urls, accuracy=2,
        threshold=0.1,
        ping_threshold=0.1,
        std_deviation_threshold=0.1,
        ping_std_deviation_threshold=0.1,
        delay=0.0,
        outfile="data/output/assess_latency/assess_latency.csv",
        verbose=False,
        # verbose=True,
    )
