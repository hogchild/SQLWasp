#!/usr/bin/env python3.12
# scratch.py
import concurrent.futures
import datetime
import functools
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console

# urls = ["https://sivanandamusic.it", "https://www.kamapuaa.it"]
# urls = ["https://google.it", "https://kamapuaa.it"]

c = Console()

futures = []

urls = [
    "http://kamapuaa.it", "https://sivanandamusic.it/", "https://sivanandamusic.it/fango", "https://google.com",
    "https://www.rainews.it/",
    "https://www.ilsole24ore.com/", "https://www.padovanet.it/", "https://yahoo.com",
    "https://dev.energiasolare100.com/",
    "https://www.duowatt.it/", "https://top10best.how/", "https://www.solar-electric.com/",
    "http://www.flexienergy.it/",
    "https://www.ginlong.com", "https://www.manomano.it/", "https://www.agrieuro.com/", "https://www.peimar.com/",
    "https://www.money.it/", "https://tg24.sky.it/", "https://www.maranza.net", "https://www.val-pusteria.net/",
    "https://www.riopusteria.it/", "https://accademiadellacrusca.it/", "https://www.wired.it/",
    "https://milano.corriere.it/", "https://www.suedtirolerland.it", "https://www.valleisarco.net",
    "https://www.maranza.org/", "https://www.dolomititour.com/", "https://www.expedia.it", "https://www.tavolla.com/",
    "https://www.vectronenergia.it", "https://climaidraulica.it", "https://mac3.it",
    "https://www.energialternativa.info", "https://mideafsc.en.made-in-china.com"
]


def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        def h_time(timestamp):
            return datetime.datetime.fromtimestamp(timestamp)

        start_time = time.time()
        c.print(f"Function '{func.__name__}' started at: {h_time(start_time)}.", style="blue bold")
        value = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        c.print("\n", f"Function '{func.__name__}' end time: {h_time(end_time)}.", style="blue bold")
        c.print(f"Completed in: {elapsed_time:.2f} seconds.", style="blue bold")
        return value

    return wrapper_timer


@timer
def fire():
    try:
        with ThreadPoolExecutor(max_workers=len(urls)) as executor:
            future: concurrent.futures.Future = concurrent.futures.Future()
            for url in urls:
                if future:
                    if future.cancelled():
                        close(executor, url)
                args = [
                    "python3", "-m",
                    "SQLWasp.assess_latency", url,  # "-v",
                    "--accuracy", "2",
                    "--delay", "0.3",
                    "--threshold", "1.0",
                    "--ping-threshold", "0.3",
                    "--std-deviation-threshold", "6.3",
                    "--ping-std-deviation-threshold", "0.1"
                ]
                future = executor.submit(subprocess.run, args)
                futures.append(future)
    except KeyboardInterrupt:
        error_message = "[+] Detected CTRL+C. Killing all processes and quitting the program."
        c.print(error_message, style="green")
        close(executor, url)


def close(executor, url):
    for future in futures:
        future.cancel()
        c.print(f"[+] Process stopped. (URL: '{url}')", style="dark_orange")
        executor.shutdown()
        c.print(f"[+] Executor shutdown (URL: '{url}')", style="dark_orange")
        c.print(f"[+] Quitting program.", style="dark_orange")
        sys.exit(0)


if __name__ == '__main__':
    fire()
