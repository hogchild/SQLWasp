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
    "http://kamapuaa.it", "https://sivanandamusic.it/", "https://sivanandamusic.it/fango", "https://google.com",
    "https://www.rainews.it/",
    "https://www.ilsole24ore.com/", "https://www.padovanet.it/", "https://yahoo.com",
    "https://dev.energiasolare100.com/",
    "https://www.duowatt.it/", "https://top10best.how/", "https://www.solar-electric.com/", "http://www.flexienergy.it/"
]

# urls = ["https://google.it", "https://kamapuaa.it"]


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


# @timer
def fire_assess_latency(target_url,
                        accuracy=2,
                        threshold=0.1,
                        ping_threshold=0.1,
                        std_deviation_threshold=0.1,
                        ping_std_deviation_threshold=0.1,
                        delay=1.0,
                        outfile="data/output/assess_latency/assess_latency.csv",
                        verbose=True, ):
    lat_ass = AssessLatency(target_url,
                            accuracy,
                            threshold,
                            ping_threshold,
                            std_deviation_threshold,
                            ping_std_deviation_threshold,
                            delay,
                            outfile,
                            verbose)
    lat_ass.run()
    lat_ass.__init__()


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=len(urls)) as executor:
        for url in urls:
            future = executor.submit(
                fire_assess_latency,
                url,
                accuracy=2,
                threshold=0.1,
                ping_threshold=0.1,
                std_deviation_threshold=0.1,
                ping_std_deviation_threshold=0.1,
                delay=1.0,
                outfile="data/output/assess_latency/assess_latency.csv",
                # verbose=False,
                verbose=True,
            )
            futures.append(future)
