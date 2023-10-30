#!/usr/bin/env python3.12
# assess_latency_looper.py
"""
This script is a multithreading looper for the 'AssessLatency' class. It takes the same options as the
assess_latency.py script, but the 'url' parameter is here replaced with a list of URLs ('urls') instead of one.
It sends concurrent GET and ping requests, simultaneously to all the URLs in the list and returns the final
reports of the AssessLatency class, together with a RandomForestClassifier prediction of the communication quality
with the webapp. This script only launches the 'AssessLatency' class, executes it for all URLs in the list,
then returns the 'AssessLatency' class results. The output data is written to
'data/output/assess_latency/assess_latency.csv' (by the AssessLatency class) and then the data is used to
train the model with the 'ai_matrix.py' script. It is also written to 'data/input/ai/assess_latency/assess_latency.csv',
where only the latest run's results are present so that the model can evaluate the data and make the prediction. This
happens in file 'ai.py'
"""

import datetime
import functools
import random
import sys
import time
import warnings
from concurrent.futures import Future, ThreadPoolExecutor
from queue import Queue
from threading import Lock

import click
import numpy as np
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
    "https://www.energialternativa.info", "https://mideafsc.en.made-in-china.com", "https://www.pampanorama.it",
    "https://www.treccani.it/", "https://www.nneditore.it/", "https://dizionari.corriere.it",
    "https://www.panoramagolf.it", "http://www.panorama.com.al", "https://www.campingpanorama.it",
    "https://www.doveconviene.it", "https://www.panoramadelgarda.it", "https://quadriennalediroma.org",
    "https://dizionari.repubblica.it", "https://www.hotelpanorama.to", "https://italics.art"
]

# urls_list = ["https://kamapuaa.it"]

c = Console()


def timer(func):
    """
    Timer \n
    The timer decorator will time any function decorated with it.
    It states the start, the end and the elapsed time.
    :param func: Any function
    :return: Any
    """
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
    """
    The Looper Class \n
    The Looper class is a multithreading handler for the AssessLatency class. It can launch from 2 to 12
    concurrent instances of the AssesLatency class and return its results. It can be passed arguments via
    command line. See '--help' for more info.
    """
    def __init__(self, urls: list, accuracy=2, threshold=0.1, ping_threshold=0.1, std_deviation_threshold=0.1,
                 ping_std_deviation_threshold=0.1, delay=0.3, outfile="test.csv", verbose=False,
                 max_threads=12) -> None:
        """
        This method instantiates the Looper class. \n
        Following the options that are available:
        :param urls: A list of URLs to test.
        :param accuracy: Number of requests (GET and ping) to send to each URL.
        :param threshold: The +/- number the latency can fall far from the mean.
        :param ping_threshold: The +/- number the latency can fall far from the mean.
        :param std_deviation_threshold: The value over which the std deviation should not go.
        :param ping_std_deviation_threshold: The value over which the ping std deviation should not go.
        :param delay: The delay to apply between requests (GETs and pings are sent simultaneously).
        :param outfile: The file path to write result data to.
        :param verbose: Use for extra verbosity from AssessLatency class.
        :param max_threads: Number of threads the Looper class has to use (min 2, max 12).
        """
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
        self.final_table = Table()
        self.test_passed = 0
        self.ai_prediction = None
        self.right_predictions = []
        self.wrong_predictions = []

    def _print_ai_prediction_assessment(self):
        """
        5th to be called. \n
        This method compares the actual results from the results (derived from the calculations
        of latencies) with the prediction made by the AI model (RandomForestClassifier), about
        the outcome of the test.
        :return:
        """
        self.c.print(
            Markdown(
                f"---\n\n"
                f"**Total predictions:** '{len(self.wrong_predictions) + len(self.right_predictions)}' \n"
                f"**Total Right Predictions:** '{len(self.right_predictions)}' \n"
                f"**Total Wrong Predictions:** '{len(self.wrong_predictions)}' \n\n"
                f"---\n\n"
            ), style="green", highlight=True
        )

    def _print_results(self):
        """
        [HELPER METHOD] (called from 4th). \n
        'self.parse_results' helper method to print results.
        Prints out a Markdown table with the results from the test and the AI prediction,
        after each table (rich Table) with all the values from the GET and ping responses analysis.
        :return: None
        """
        self.c.print(
            self.final_table, Markdown(
                f"| Test Outcome: | AI Prediction: |\n"
                f"| :-----------: | :------------: |\n"
                f"| {'Passed' if self.test_passed == 1 else 'Failed'} | "
                f"{'Passed' if self.ai_prediction[0] == 1 else 'Failed'} |\n\n"
            )
        )

    def parse_results(self) -> None:
        """
        4th to be called. \n
        Retrieves requests results from the queues in the 'self.futures' list of queues
        using concurrent futures threading. The 'self.futures' list is filled up with results
        after the AssessLatency class has run. This method prints these results out. Finally,
        it compares the final test result with the prediction made by the AI module.
        :return: None
        """
        try:
            with ThreadPoolExecutor(max_workers=self.max_threads) as self.executor:
                for thread_id, queue in enumerate(self.futures):
                    while not queue.empty():
                        self.future = self.futures[thread_id].get()
                        try:
                            self.final_table, self.test_passed, self.ai_prediction = self.future.result()
                            if self.test_passed == self.ai_prediction[0]:
                                self.right_predictions.append(1)
                            else:
                                self.wrong_predictions.append(0)
                        except TypeError as e:
                            self.c.print(f"TypeError in print result: {e} \nSkipping..", style="bright_red")
                            pass
                        else:
                            self._print_results()
            self._print_ai_prediction_assessment()
        except KeyboardInterrupt:
            error_message = f"Detected CTRL+C. Exiting."
            self.close(error_message, key_int=True)

    def fire(self, url) -> tuple[Table, bool, np.ndarray]:
        """
        3rd method to be called. \n
        This method instantiates the AssessLatency class and actually runs it.
        It is called by a ThreadPoolExecutor instance.
        :param url: The url on which to instantiate the AssessLatency class
        :return: None
        """
        try:
            self.latency_assessor = AssessLatency(
                url, self.accuracy, self.threshold, self.ping_threshold, self.std_deviation_threshold,
                self.ping_std_deviation_threshold, self.delay, self.outfile, self.verbose
            )
            return self.latency_assessor.run()
        except KeyboardInterrupt:
            error_message = f"Detected CTRL+C. Exiting."
            self.close(error_message, key_int=True)

    def looper(self) -> None:
        """
        2nd method to be called. \n
        It first checks if the 'self.future' instance has been 'cancelled()', maybe by a
        KeyboardInterrupt (see the 'self.close' method), if not it goes ahead and enumerates
        the 'self.get_queues', a list of queues created at the beginning. Each queue is accessible
        by 'thread_id', same as with a dictionary, really we are accessing a list by index, as the
        'thread_id' is indeed an int value, incrementing by 1 up to the value hold by the
        'self.max_threads' variable.
        :return: None
        """
        try:
            with Lock():
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

    def create_queues(self) -> None:
        """
        1st to be called. \n
        This method fills up the queues 'self.get_queues' list. It uses the round-robin method
        to assign thread_ids (1-incrementing integer up to the 'self.max_threads' value) and to
        distribute the URLs from the user provided urls list, as evenly as possible between
        the queues.
        :return: None
        """
        for i, self.url in enumerate(self.urls):
            thread_id = i % self.max_threads
            self.get_queues[thread_id].put(self.url)

    @timer
    def run(self) -> None:
        """
        Root method. \n
        This method is responsible for running the whole class. It calls all the class's
        methods in the right order.
        :return: None
        """
        self.filter_warnings()
        self.create_queues()
        self.looper()
        self.parse_results()

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
        value = int(value)
    except ValueError:
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
    default=random.randrange(2, 10, 1),
    show_default=True,
    required=True,
    type=int
)
@click.option(
    "-t", "--threshold",
    help="The delta (+/-). Determines the lowest and the highest values the response time must be within, "
         "in order to be considered a 'normal' response time (ie: <average_response_time> +/- <threshold>).",
    default=random.uniform(0.0, 6.0),
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-T", "--ping-threshold", "ping_threshold",
    help="The delta (+/-). Determines the lowest and the highest values the ping response time must be within, "
         "in order to be considered a 'normal' response time (ie: <ping_average_response_time> +/- <threshold>).",
    default=random.uniform(0.0, 6.0),
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-x", "--std-deviation-threshold", "std_deviation_threshold",
    help="The value over which the standard deviation should not go beyond"
         "without an alert being triggered.",
    default=random.uniform(0.0, 6.0),
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-y", "--ping-std-deviation-threshold", "ping_std_deviation_threshold",
    help="The value over which the ping standard deviation should not go beyond"
         "without an alert being triggered.",
    default=random.uniform(0.0, 6.0),
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-D", "--delay",
    help="The seconds to wait in between requests.",
    default=random.uniform(0.0, 2.0),
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-o", "--outfile",
    help="Specify a path where you want to save a csv with all data to.",
    # default="test.csv",
    default="data/output/assess_latency/assess_latency.csv",
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
