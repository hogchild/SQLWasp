#!/usr/bin/env python3.12
# assess_latency_looper.py

import datetime
import functools
import sys
import time
import warnings
from concurrent.futures import Future, ThreadPoolExecutor
from queue import Queue

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from SQLWasp.assess_latency import AssessLatency

urls_list = [
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

c = Console()


def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        def h_time(timestamp):
            return datetime.datetime.fromtimestamp(timestamp)

        start_time = time.time()
        c.print(f"Looper started at: {h_time(start_time)}.", style="blue")
        value = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        c.print("\n", f"Looper completed all tasks at: {h_time(end_time)}.", style="blue")
        c.print(f"Runtime: {elapsed_time:.4f} seconds.", style="blue bold")
        return value

    return wrapper_timer


class Looper:
    def __init__(self, urls, accuracy=2, threshold=0.1, ping_threshold=0.1, std_deviation_threshold=0.1,
                 ping_std_deviation_threshold=0.1, delay=0.3, outfile="test.csv", verbose=False,
                 max_threads=12):
        self.c = Console()
        self.urls = urls
        self.url = None
        self.latency_assessor = None
        self.accuracy = accuracy
        self.threshold = threshold
        self.ping_threshold = ping_threshold
        self.std_deviation_threshold = std_deviation_threshold
        self.ping_std_deviation_threshold = ping_std_deviation_threshold
        self.delay = delay
        self.outfile = outfile
        self.verbose = verbose
        self.max_threads = max_threads
        self.get_queues = [Queue() for _queue in range(self.max_threads)]
        self.futures = [Queue() for _queue in range(self.max_threads)]
        self.future = Future()
        self.table = Table()
        self.test_passed = 0
        self.ai_prediction = None
        self.right_predictions = []
        self.wrong_predictions = []

    def print_results(self):
        try:
            with ThreadPoolExecutor(max_workers=self.max_threads) as self.executor:
                for thread_id, queue in enumerate(self.futures):
                    while not queue.empty():
                        self.future = self.futures[thread_id].get()
                        try:
                            self.table, self.test_passed, self.ai_prediction = self.future.result()
                        except TypeError as e:
                            self.c.print(f"TypeError in print result: {e} \nSkipping..", style="bright_red")
                            pass
                        self.c.print(
                            self.table, Markdown(
                                f"| Test Outcome: | AI Prediction: |\n"
                                f"| :-----------: | :------------: |\n"
                                f"| {'Passed' if self.test_passed == 1 else 'Failed'} | "
                                f"{'Passed' if self.ai_prediction[0] == 1 else 'Failed'} |\n\n"
                            )
                        )
                        if self.test_passed == self.ai_prediction[0]:
                            self.right_predictions.append(1)
                        else:
                            self.wrong_predictions.append(0)
            self.c.print(
                Markdown(
                    f"---\n\n"
                    f"**Total predictions:** '{len(self.wrong_predictions) + len(self.right_predictions)}' \n"
                    f"**Total Right Predictions:** '{len(self.right_predictions)}' \n"
                    f"**Total Wrong Predictions:** '{len(self.wrong_predictions)}' \n\n"
                    f"---\n\n"
                ), style="green", highlight=True
            )

        except KeyboardInterrupt:
            error_message = f"Detected CTRL+C. Exiting."
            self.close(error_message, key_int=True)

    def fire(self, url):
        try:
            self.latency_assessor = AssessLatency(
                url, self.accuracy, self.threshold, self.ping_threshold, self.std_deviation_threshold,
                self.ping_std_deviation_threshold, self.delay, self.outfile, self.verbose
            )
            return self.latency_assessor.run()
        except KeyboardInterrupt:
            error_message = f"Detected CTRL+C. Exiting."
            self.close(error_message, key_int=True)

    def looper(self):
        try:
            with ThreadPoolExecutor(max_workers=12) as self.executor:
                if self.future.cancelled():
                    self.close("")
                for thread_id, queue in enumerate(self.get_queues):
                    while not queue.empty():
                        self.url = self.get_queues[thread_id].get()
                        self.future = self.executor.submit(self.fire, self.url)
                        self.futures[thread_id].put(self.future)
        except KeyboardInterrupt:
            error_message = f"Detected CTRL+C. Exiting."
            self.close(error_message, key_int=True)

    def create_queues(self):
        for i, self.url in enumerate(self.urls):
            thread_id = i % self.max_threads
            self.get_queues[thread_id].put(self.url)

    @timer
    def run(self):
        self.filter_warnings()
        self.create_queues()
        self.looper()
        self.print_results()

    def filter_warnings(self):
        warnings.filterwarnings("ignore", category=UserWarning)

    def close(self, error_message, key_int=False):
        if key_int:
            self.c.print("\n", f"Detected CTRL+C. Exiting.", style="dark_orange")
        else:
            self.c.print(error_message, style="dark_orange")
        for thread_id, queue in enumerate(self.futures):
            while not queue.empty():
                self.future = self.futures[thread_id].get()
                self.future.cancel()
        self.executor.shutdown()
        sys.exit(0)


def validate_max_threads(ctx, param, value):
    try:
        print(value)
        value = int(value)
    except ValueError as e:
        error_message = f"Invalid literal {value}. Please enter a valid integer between 2 and 12."
        raise click.BadParameter(error_message)
    else:
        if isinstance(value, int):
            if 2 <= value <= 12:
                return value
        else:
            raise click.BadParameter(f"Insert a valid integer between 2 and 12.")


@click.command(
    help="This tool sends a specified number of GET requests, to a target URL, "
         "and measures the response time. It then makes an average and compares it to a specified "
         "threshold value (threshold: float). It return an evaluation of the fluidity of the communication "
         "with the web application."
)
# @click.argument(
#     "url",
#     nargs=1,
#     metavar="URL",
#     required=True,
#     default="https://kamapuaa.it",
#     type=str
# )
@click.option(
    "-u", "--urls",
    help="A list of URLs that will be tested.",
    default=urls_list,
    required=True,
    type=list
)

@click.option(
    "-a", "--accuracy",
    help="The number of GET requests that will be sent to perform the analysis. "
         "The highest the number, the slowest the test, the more accurate the response.",
    default=10,
    show_default=True,
    required=True,
    type=int
)
@click.option(
    "-t", "--threshold",
    help="The delta (+/-). Determines the lowest and the highest values the response time must be within, "
         "in order to be considered a 'normal' response time (ie: <average_response_time> +/- <threshold>).",
    default=0.1,
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-T", "--ping-threshold", "ping_threshold",
    help="The delta (+/-). Determines the lowest and the highest values the ping response time must be within, "
         "in order to be considered a 'normal' response time (ie: <ping_average_response_time> +/- <threshold>).",
    default=0.1,
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-x", "--std-deviation-threshold", "std_deviation_threshold",
    help="The value over which the standard deviation should not go beyond"
         "without an alert being triggered.",
    default=0.3,
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-y", "--ping-std-deviation-threshold", "ping_std_deviation_threshold",
    help="The value over which the ping standard deviation should not go beyond"
         "without an alert being triggered.",
    default=0.3,
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-D", "--delay",
    help="The seconds to wait in between requests.",
    default=0.3,
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-o", "--outfile",
    help="Specify a path where you want to save a csv with all data to.",
    default="test.csv",
    # default="data/output/assess_latency/assess_latency.csv",
    show_default=True,
    required=False,
    type=click.Path()
)
@click.option(
    "-v", "--verbose",
    help="Use for verbosity.",
    is_flag=True,
    default=False,
    required=False,
    type=bool
)
@click.option(
    "-m", "--max-threads", "max_threads",
    help="Max number of concurrent threads (max 12).",
    default=12,
    required=True,
    type=click.UNPROCESSED,
    callback=validate_max_threads
)
def main(urls, accuracy, threshold, ping_threshold, std_deviation_threshold,
         ping_std_deviation_threshold, delay, outfile, verbose, max_threads):
    looper = Looper(urls, accuracy, threshold, ping_threshold, std_deviation_threshold,
                    ping_std_deviation_threshold, delay, outfile, verbose, max_threads)
    looper.run()


if __name__ == "__main__":
    main()
