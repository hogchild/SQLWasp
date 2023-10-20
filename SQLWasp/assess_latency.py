#!/usr/bin/env python3.12
# assess_latency.py

"""
This module assesses a web-application's response latency. It uses the requests library to repeatedly
send get requests to a given URL and appends the results in a list, which will later be used for
various calculations (based on the response times to the requests), to determine the quality of the
communication with the web app.
"""
import functools
import statistics
import sys
import time
# from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fractions import Fraction

import click
import requests
from rich.console import Console
from rich.markdown import Markdown

from SQLWasp.custom_errors import CheckLatencyConsistencyError, AssessURLRequestError
from data.input.data_sources import standard_deviation_tab, response_latency_status_tab


def timer(func):
    """
    Decorator that appends the response times (ie: the decorated func runtime),
    to the 'self.latencies_list'.
    :param func:
    :return:
    """

    @functools.wraps(func)
    def wrapper_timer(self, *args, **kwargs):
        start_time = time.time()
        value = func(self, *args, **kwargs)
        end_time = time.time()
        latency = end_time - start_time
        self.latencies_list.append(latency)
        return value

    return wrapper_timer


class AssessLatency:
    def __init__(self, url: str, accuracy: int = 7, threshold: float = 0.4,
                 std_deviation_threshold: float = 0.1, verbose: bool = False) -> None:
        self.c = Console()
        self.verbose = verbose
        self.result_tab = standard_deviation_tab
        self.response_latency_status_tab = response_latency_status_tab
        self.url = url
        self.accuracy = accuracy
        self.threshold = threshold
        self.bottom_threshold = 0.0
        self.top_threshold = 0.0
        self.std_deviation_threshold = std_deviation_threshold
        self.response = None
        self.latencies_list = []
        self.responses_list = []
        self.std_deviation = 0.0
        self.latency_average = 0.0
        self.test_passed = False

    def network_test_passed(self) -> bool:
        if self.std_deviation < self.std_deviation_threshold:
            if self.bottom_threshold < self.latency_average <= self.top_threshold:
                self.test_passed = True
                return self.test_passed
        else:
            self.test_passed = False
            return self.test_passed

    def check_latency_consistency(self) -> str:
        """
        5th to be called. \n
        It uses the statistics library to calculate the standard deviation,
        which is how much a value gets distant from the average. It may be
        valuable information to understand if the web application's responses
        are received with fluidity, or they arrive to us irregularly, which
        might indicate problems with the web app, or the network.
        :return: 'self.result_tab'. A tab:
        Max Value | Min Value | Standard Deviation | Current Deviation Threshold Value.
        """
        # Calculate the standard deviation
        try:
            self.std_deviation = statistics.stdev(self.latencies_list)
        except statistics.StatisticsError as e:
            error_message = f"Unable to test latency consistency: {e}"
            raise CheckLatencyConsistencyError(error_message) from e
        # Set a threshold for what you consider "regular"
        # threshold = 0.1  # You can adjust this value based on your specific needs
        # Check if the standard deviation is below the threshold
        if self.std_deviation < self.std_deviation_threshold:
            message = f"[+] The values are relatively consistent."
            if self.verbose:
                self.c.print("\n", message, style="green")
            record = (f"| {max(self.latencies_list):.3f} | {min(self.latencies_list):.3f} | {self.std_deviation} "
                      f"| {self.std_deviation_threshold} | \n")
            self.result_tab += record
            return self.result_tab
        else:
            message = "[-] The values vary significantly. Consider adjusting the deviation threshold value."
            if self.verbose:
                self.c.print("\n", message, style="dark_orange")
            record = (
                f"| {max(self.latencies_list):.3f} | {min(self.latencies_list):.3f} | {self.std_deviation} "
                f"| {self.std_deviation_threshold} | \n")
            self.result_tab += record
            return self.result_tab

    def get_response_latency_status(self) -> str:
        """
        4th to be called. \n
        It parses top and bottom threshold value from 'self.threshold', which
        represents the delta (+/-), the lowest and the highest values, the
        response time must be within, in order to be considered a normal response
        time.
        :return: 'self.response_latency_status_tab': | Average Response Time | Current Threshold Value |.
        """
        self.bottom_threshold = self.latency_average - self.threshold
        self.top_threshold = self.latency_average + self.threshold
        if not self.bottom_threshold < self.latency_average <= self.top_threshold:
            message = (
                f"[-] Web application response is a bit slow. "
                f"You might want to consider increasing the threshold value. \n"
            )
            if self.verbose:
                self.c.print(Markdown(message), style="dark_orange")
            record = f"| {self.latency_average} | {self.threshold} | \n"
            self.response_latency_status_tab += record
            return self.response_latency_status_tab
        else:
            message = (
                f"[+] Web application response is normal. "
            )
            if self.verbose:
                self.c.print(Markdown(message), style="green")
            record = f"| {self.latency_average} | {self.threshold} | \n"
            self.response_latency_status_tab += record
            return self.response_latency_status_tab

    def process_latency_average(self) -> float | Decimal | Fraction:
        """
        3rd to be called. \n
        It calculates the mean between all the
        time values appended from the '\\@timer' decorator. These are the runtimes
        of the 'self._assess_url' method, essentially the response times to our
        GET requests:
        :return: 'self.latency_average'. The mean of the time values in 'self.latencies_list'.
        """
        self.latency_average = statistics.mean(self.latencies_list)
        return self.latency_average

    @timer
    def _assess_url(self) -> requests.Response:
        """
        2nd to be called. \n
        It's a helper of the 'self.assess_url()' method.
        It takes care of sending a GET requests to the 'self.url' URL and store its response
        in the 'self.response' variable. The '@timer' decorator takes care of the response times.
        :return: 'self.response'
        """
        try:
            self.response = requests.get(self.url)
        except requests.RequestException as e:
            error_message = f"Request failed: {e}"
            raise AssessURLRequestError(error_message) from e
        else:
            return self.response

    def assess_url(self) -> list[dict]:
        """
        1st to be called.\n
        This method creates a list of dictionaries, with the request ids as keys and
        the associated response to the GET request as values. It does so by means of
        the 'self._assess_url()' helper method, which actually takes care of sending
        the requests and storing the responses in the 'self.response' instance variable.\n
        Note: 'self.accuracy' is the number of requests over which the assessment will be taken.
        :return: 'self.responses_list' -> [{"RequestId": requests.Response}]
        """
        for req_id, scan in enumerate(range(self.accuracy)):
            # with ThreadPoolExecutor(max_workers=self.accuracy) as executor:
            #     remaining = self.accuracy
            #     while remaining:
            #         print("start")
            #         future = executor.submit(
            #             self.responses_list.append,
            #             {f"RequestId_{req_id}": self._assess_url()},
            #         )
            #         remaining -= 1
            #         print(future.result())
            self.responses_list.append({f"RequestId_{req_id}": self._assess_url()})
        return self.responses_list

    def run(self) -> bool:
        """
        Method 0 \n
        This is the central method, the one that calls , in order, all the other
        required methods, so for the class to initialize and run.
        :return: None
        """
        try:
            self.assess_url()
        except AssessURLRequestError as e:
            error_message = f"[-] AssessURL Run Error: {e}"
            self.close(error_message)
        self.process_latency_average()
        self.c.print(Markdown(self.get_response_latency_status()))
        try:
            self.c.print(Markdown(self.check_latency_consistency()))
        except CheckLatencyConsistencyError as e:
            error_message = f"[-] AssessUrl Run Error: {e}.\n* Hint: Accuracy option ('-a') must be greater than 1."
            self.close(error_message)
        else:
            self.c.print(self.network_test_passed())
        return self.test_passed

    def close(self, error_message):
        self.c.print(Markdown(error_message), style="red")
        self.c.print("\n", Markdown("Use --help for more information or read the README.md file."))
        sys.exit(1)


@click.command(
    help="This tool sends a specified number of GET requests, to a target URL, "
         "and measures the response time. It then makes an average and compares it to a specified "
         "threshold value (threshold: float). It return an evaluation of the fluidity of the communication "
         "with the web application."
)
@click.argument(
    "url",
    nargs=1,
    metavar="URL",
    required=True,
    default="https://kamapuaa.it",
    type=str
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
         "in order to be considered a normal response time (ie: <average_response_time> +/- <threshold>).",
    default=0.2,
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-d", "--std-deviation-threshold", "std_deviation_threshold",
    help="The value over which the standard deviation should not go beyond"
         "without an alert being triggered.",
    default=0.1,
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-v", "--verbose",
    help="Use for verbosity.",
    is_flag=True,
    default=False,
    required=False,
    type=bool
)
def main(url: str, accuracy, threshold, std_deviation_threshold, verbose: bool):
    lat_ass = AssessLatency(url, accuracy, threshold, std_deviation_threshold, verbose=verbose)
    test_passed = lat_ass.run()
    return test_passed


if __name__ == '__main__':
    main()
