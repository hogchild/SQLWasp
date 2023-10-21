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
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fractions import Fraction

import click
import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

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
                 std_deviation_threshold: float = 0.1, delay: float = None, verbose: bool = False) -> None:
        self.c = Console()
        self.verbose = verbose
        self.result_tab = standard_deviation_tab
        self.response_latency_status_tab = response_latency_status_tab
        self.futures = []
        self.future = None
        self.url = url
        self.accuracy = accuracy
        self.threshold = threshold
        self.delay = delay
        self.bottom_threshold = 0.0
        self.top_threshold = 0.0
        self.std_deviation_threshold = std_deviation_threshold
        self.response = None
        self.latencies_list = []
        self.responses_list = []
        self.std_deviation = 0.0
        self.latency_average = 0.0
        self.test_passed = False
        self.final_table = None
        self.status_codes = {}

    def generate_report(self) -> Table:
        """
        7th to be called. \n
        Creates and returns a table, using the rich library
        and its 'Table' class. The table contains all the data
        calculated during runtime.
        :return: Report Table with all the elaborated data.
        """
        self.final_table = Table(title="Final Report Table", title_style="bold")
        self.final_table.add_column(header="Data", style="bold")
        self.final_table.add_column(header="Value", style="bold")
        self.final_table.add_row("Number of Requests Sent", str(self.accuracy), style=None)
        self.final_table.add_row("Requests Delay", f"{self.delay} secs", style=None)
        self.final_table.add_row("Communication Quality Threshold", f"{self.threshold} sec")
        self.final_table.add_row("Standard Deviation Threshold", f"{self.std_deviation_threshold} sec")
        self.final_table.add_row("Latency Average", f"{self.latency_average} secs")
        self.final_table.add_row("Standard Deviation", f"{self.std_deviation} secs")
        for status_code_category, response in self.status_codes.items():
            self.final_table.add_row(
                f"Status Code: {status_code_category}",
                f"Number of Responses: {str(len(self.status_codes.get(status_code_category)))}"
            )
        self.final_table.add_row("Test Passed", str(self.test_passed))
        return self.final_table

    def network_test_passed(self) -> bool:
        """
        7th to be called. \n
        This method evaluates the results and returns a bool response.
        True if, from the elaborated data, the communication with the
        web application is considered good enough for the intended
        purpose (in this case Cookie SQL Injection Vulnerability
        Discovery). Otherwise, it will return False.
        :return: bool | True: Good Communication | False: Bad Communication
        with the server.
        """
        if self.std_deviation < self.std_deviation_threshold:
            if self.bottom_threshold < self.latency_average <= self.top_threshold:
                for k in self.status_codes.keys():
                    if k == 200:
                        self.test_passed = True
                        return self.test_passed
                    else:
                        self.test_passed = False
                        return self.test_passed
            else:
                self.test_passed = False
                return self.test_passed
        else:
            self.test_passed = False
            return self.test_passed

    def check_latency_consistency(self) -> str:
        """
        6th to be called. \n
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
        # 'self.std_deviation_threshold' = 0.1 (or whatever)  # You can adjust this value based on your specific needs
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
        5th to be called. \n
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
        4th to be called. \n
        It calculates the mean between all the
        time values appended from the '\\@timer' decorator. These are the runtimes
        of the 'self._assess_url' method, essentially the response times to our
        GET requests:
        :return: 'self.latency_average'. The mean of the time values in 'self.latencies_list'.
        """
        self.latency_average = statistics.mean(self.latencies_list)
        return self.latency_average

    def process_status_codes(self) -> dict:
        """
        3rd to be called. \n
        This method iterates through the response dictionary, where all the
        futures are stored under their 'request id', extracts the response
        status code from each of them. It creates a dictionary with the found
        response codes as keys, and a list with each found response of that code.
        :return: 'self.status_codes': dict of found responses status codes.
        """
        for req_dict in self.responses_list:
            for _request_id, future in req_dict.items():
                response: requests.Response = future.result()
                status_code = response.status_code
                if self.status_codes.get(status_code) is None:
                    self.status_codes[status_code] = []
                self.status_codes[status_code].append(response)
        return self.status_codes

    @timer
    def _assess_url(self, req_id) -> requests.Response:
        """
        2nd to be called. \n
        It's a helper of the 'self.assess_url()' method.
        It takes care of sending a GET requests to the 'self.url' URL and store its response
        in the 'self.response' variable. The '@timer' decorator takes care of the response times.
        :return: 'self.response'
        """
        try:
            self.response = requests.get(self.url)
        except requests.exceptions.RequestException as e:
            error_message = f"Request failed: {e}"
            self.close(error_message)
        else:
            self.c.print(f"Response {req_id}: {self.response}")
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
        try:
            with ThreadPoolExecutor(max_workers=self.accuracy) as executor:
                for req_id, scan in enumerate(range(self.accuracy)):
                    if self.future:
                        if not self.future.cancelled():
                            self.c.print(f"future status: {self.future.cancelled()}", style="blue")

                    self.future = executor.submit(self._assess_url, req_id)
                    if self.delay:
                        time.sleep(self.delay)
                    self.responses_list.append({f"RequestId_{req_id}": self.future})
                    self.futures.append(self.future)
                    self.c.print(f"Sent request {req_id}.")
                return self.responses_list
        except KeyboardInterrupt:
            self.close("Detected CTRL+C. Bye.")

    def run(self) -> bool:
        """
        Method 0 \n
        This is the central method, the one that calls , in order, all the other
        required methods, so for the class to initialize and run.
        :return: None
        """
        # Send the GET requests using ThreadPoolExecutor
        try:
            self.assess_url()
        except AssessURLRequestError as e:
            error_message = f"[-] AssessURL Run Error: {e}"
            self.close(error_message)
        self.process_status_codes()
        self.process_latency_average()
        self.c.print(Markdown(self.get_response_latency_status()))
        try:
            self.c.print(Markdown(self.check_latency_consistency()))
        except CheckLatencyConsistencyError as e:
            error_message = f"[-] AssessUrl Run Error: {e}.\n* Hint: Accuracy option ('-a') must be greater than 1."
            self.close(error_message)
        else:
            self.c.print(f"Test Passed: {self.network_test_passed()} \n")
            self.c.print(f"Generating report. \n", self.generate_report())
        return self.test_passed

    def kill_all_threads(self):
        for future in self.futures:
            future.cancel()

    def close(self, error_message) -> None:
        """
        Closing method. \n
        It prints the error message passed as an argument,
        then the advice to check out --help.
        Finally, exits the program.
        :param error_message: error message passed in when error raised
        :return: None. Exit messages & Exit.
        """
        self.kill_all_threads()
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
    default=0.1,
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
    "-D", "--delay",
    help="The seconds to wait in between requests.",
    default=0.0,
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
def main(url: str, accuracy, threshold, std_deviation_threshold, delay, verbose: bool):
    lat_ass = AssessLatency(url, accuracy, threshold, std_deviation_threshold, delay, verbose=verbose)
    test_passed = lat_ass.run()
    # responses_list = lat_ass.responses_list
    return test_passed


if __name__ == '__main__':
    main()
