#!/usr/bin/env python3.12
# assess_latency.py

"""
This module assesses a web-application's response latency. It uses the requests library to repeatedly
send get requests to a given URL and appends the results in a list, which will later be used for
various calculations (based on the response times to the requests), to determine the quality of the
communication with the web app.
"""

import functools
import os.path
import socket
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from queue import Queue
from threading import Lock
from urllib.parse import urlparse

import click
import numpy as np
import pandas
import pandas as pd
import requests
from ping3 import ping
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from SQLWasp.ai import AIControl
from SQLWasp.custom_errors import CheckLatencyConsistencyError, AssessURLRequestError
from data.input.data_sources import standard_deviation_tab, response_latency_status_tab, \
    ping_response_latency_status_tab, http_status_codes

ai_data_bucket_path = "data/input/ai/assess_latency/assess_latency.csv"


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
    """
    This class is designed to assess the quality of the communication of a specified web app (at a given URL).
    It does so by sending GET an ICMP requests to a given URL, then makes calculations of average response
    times and standard deviations, results of which are taken into consideration to assess the quality of the
    communication. It has to be used with the 'SQLWasp.assess_latency_looper' for best result and speed. This
    class and the Looper class are multithreaded.
    """

    def __init__(self, url: str, accuracy: int = 10, threshold: float = 0.1, ping_threshold: float = 0.1,
                 std_deviation_threshold: float = 0.1, ping_std_deviation_threshold: float = 0.1, delay: float = 0.0,
                 outfile: Path | str = None, verbose: bool = False) -> None:
        """
        This method instantiates the AssessLatency class.
        :param url: The URL that will be tested.
        :param accuracy: The number of requests (GET and ICMP) that will be sent.
        :param threshold: The +/- number below and abow the latency mean used to establish latency acceptability.
        :param ping_threshold: Same as threshold but for ICMP requests.
        :param std_deviation_threshold: The standard deviation value that should not be reached and go over.
        :param ping_std_deviation_threshold: Same as std_deviation_threshold but for ICMP requests.
        :param delay: The amount of second to sleep between a request and the next.
        :param outfile: The path of the output file, appended with new data each run. Used to train the model.
        :param verbose: Use for extra verbosity (under development...).
        """
        self.c = Console()
        self.outfile = outfile
        self.verbose = verbose
        self.result_tab = standard_deviation_tab
        self.response_latency_status_tab = response_latency_status_tab
        self.ping_response_latency_status_tab = ping_response_latency_status_tab
        self.futures = []
        self.ping_futures = []
        self.future = None
        self.ping_future = None
        self.url = url
        self.host = self.get_host_name()
        self.accuracy = accuracy
        self.threshold = threshold
        self.ping_threshold = ping_threshold
        self.delay = delay
        self.bottom_threshold = 0.0
        self.top_threshold = 0.0
        self.ping_bottom_threshold = 0.0
        self.ping_top_threshold = 0.0
        self.std_deviation_threshold = std_deviation_threshold
        self.ping_std_deviation_threshold = ping_std_deviation_threshold
        self.response = None
        self.ping_reply = None
        self.latencies_list = []
        self.ping_latencies_list = []
        self.responses_list = []
        self.ping_responses_list = []
        self.std_deviation = 0.0
        self.ping_std_deviation = 0.0
        self.latency_mean = 0.0
        self.ping_latency_mean = 0.0
        self.test_results = []
        self.test_passed = False
        self.test_final_evaluation = None
        self.final_table: Table = Table()
        self.table_data = []
        self.ai_prediction = None
        self.status_codes = http_status_codes
        self.ai_data_bucket_path = ai_data_bucket_path
        self.trained_ai_model_path = "data/input/ai/net_watcher.pkl"
        self.input_data_csv_path = "data/input/ai/assess_latency/assess_latency.csv"
        self.queues = [Queue() for _queue in range(self.accuracy)]

    # CHECK DOCSTRING FOR MODIFICATION SUGGESTIONS.
    def get_host_name(self) -> str:
        """
        Called from '__init__'. \n
        This method parses the IP address of the scanned URL. \n
        **Note**: CONSIDER PASSING THE HOSTNAME IF IP UNAVAILABLE. \n
        :return: The IP Address of the URL or quits.
        """
        host_name = urlparse(self.url).hostname
        try:
            return socket.gethostbyname(
                host_name)
        except socket.gaierror as e:
            error_message = (f"Unable to parse {host_name} IP address: {e}. "
                             f"Using hostname for ICMP (ping) requests.")
            self.c.print(error_message, style="cyan")
            return host_name
            # sys.exit(1)

    def ai_confirm(self) -> np.ndarray:
        """
        16th to be called. \n
        This method instantiates the AIControl class and returns the prediction
        from the trained model 'SQLWasp.ai'.
        :return: A NumPy array with just one value at index 0.
        """
        ai = AIControl(self.trained_ai_model_path, self.input_data_csv_path, self.outfile)
        ai.run()
        return ai.predictions

    def clear_status_codes(self) -> None:
        """
        15th to be called. \n
        It empties all the list for each status code (key) in the dictionary.
        :return: none
        """
        for status_code_category in self.status_codes.keys():
            self.status_codes[status_code_category] = []

    def _create_pandaz_table(self) -> list[list]:
        """
        14th to be called. \n
        Creates and returns a table including all the data resulted from
        the analysis.
        \n**Note**:\n* 'self.status_codes' is reset empty here.
        :return:
        """
        # Create the table.
        table_data = [
            ["GET Sent", self.accuracy],
            ["Ping Sent", self.accuracy],
            ["Delay", self.delay],
            ["Threshold", self.threshold],
            ["Ping Threshold", self.ping_threshold],
            ["Std Dev Threshold", self.std_deviation_threshold],
            ["Ping Std Dev Threshold", self.ping_std_deviation_threshold],
            ["GET Latency Average", self.latency_mean],
            ["Min GET Latency", min(self.latencies_list)],
            ["Max GET Latency", max(self.latencies_list)],
            ["Ping Latency Average", self.ping_latency_mean],
            ["Min Ping Latency", min(self.ping_latencies_list)],
            ["Max Ping Latency", max(self.ping_latencies_list)],
            ["Std Dev", self.std_deviation],
            ["Ping Std Dev", self.ping_std_deviation],
        ]
        for status_code_category, response in self.status_codes.items():
            table_data.append(
                [f"{status_code_category}", len(response)]
            )
        # Empty 'self.status_codes' dictionary for garbage collection.
        self.clear_status_codes()
        table_data.append(["Test Final Evaluation", self.test_final_evaluation])
        table_data.append(["Test Passed", self.test_passed])
        return table_data

    def pandaz(self) -> pandas.DataFrame:
        """
        13th to be called. \n
        It creates a table with the analysis data similar to the report in
        'self.generate_report', then uses it to create a pandas DataFrame and
        returns it.
        :return: A pandas DataFrame with tests data.
        """
        # Create table with data, make it a dictionary and put it inside a list for pandas.
        table_data = self._create_pandaz_table()
        table_dict = [dict(table_data)]
        # Create the DataFrame.
        df = pd.DataFrame(table_dict)
        return df

    def write_csv_file(self) -> pandas.DataFrame:
        """
        12th to be called. \n
        Writes analysis data from a pandas DataFrame to 2 CSV files.
        One is the outfile, which is appended with new info every run,
        and it's used also to train the AI model using 'SQLWasp.ai_matrix'
        :return: A pandas DataFrame with tests data.
        """
        # Generate the pandas DataFrame.
        pandas_dataframe = self.pandaz()
        if os.path.exists(self.outfile):
            pandas_dataframe.to_csv(self.outfile, mode="a", index=False, header=False)
        else:
            pandas_dataframe.to_csv(self.outfile, index=False)
        pandas_dataframe.to_csv(self.ai_data_bucket_path, index=False)
        return pandas_dataframe

    def generate_report(self) -> Table:
        """
        11th to be called. \n
        Creates and returns a table, using the rich library
        and its 'Table' class. The table contains all the data
        calculated during runtime.
        :return: 'self.final_table'. Report Table with all the elaborated data.
        """
        # Give the table a title
        self.final_table = Table(title="Final Report Table", title_style="bold")
        # Add table columns
        self.final_table.add_column(header="Data", style="bold")
        self.final_table.add_column(header="Value", style="bold")
        # Add table rows with calculated data.
        self.final_table.add_row("URL", str(self.url), style=None)
        self.final_table.add_row("Host", str(self.host), style=None)
        self.final_table.add_row("GET Requests Sent", str(self.accuracy), style=None)
        self.final_table.add_row("Ping Requests Sent", str(self.accuracy), style=None)
        self.final_table.add_row("Requests Delay", f"{self.delay} secs", style=None)
        self.final_table.add_row("Threshold", f"{self.threshold} sec")
        self.final_table.add_row("Ping Threshold", f"{self.ping_threshold} sec")
        self.final_table.add_row("Standard Deviation Threshold", f"{self.std_deviation_threshold} sec")
        self.final_table.add_row("Ping Standard Deviation Threshold", f"{self.ping_std_deviation_threshold} sec")
        self.final_table.add_row("GET Latency Mean", f"{self.latency_mean} secs")
        self.final_table.add_row("Min GET Latency", f"{min(self.latencies_list)} secs")
        self.final_table.add_row("Max GET Latency", f"{max(self.latencies_list)} secs")
        self.final_table.add_row("Ping Latency Mean", f"{self.ping_latency_mean} secs")
        self.final_table.add_row("Min Ping Latency", f"{min(self.ping_latencies_list)} secs")
        self.final_table.add_row("Max Ping Latency", f"{max(self.ping_latencies_list)} secs")
        self.final_table.add_row("Standard Deviation", f"{self.std_deviation} secs")
        self.final_table.add_row("Ping Standard Deviation", f"{self.ping_std_deviation} secs")
        #
        for status_code_category, response in self.status_codes.items():
            self.final_table.add_row(
                f"Status Code: {status_code_category}",
                f"Responses received: {str(len(self.status_codes.get(status_code_category)))}"
            )
        self.final_table.add_row("Test Final Evaluation", str(self.test_final_evaluation))
        self.final_table.add_row("Test Passed", str("True" if self.test_passed else "False"), style="blink")
        return self.final_table

    def validate_test(self) -> tuple[int, float]:
        """
        10th to be called. \n
        This is essentially a helper function of the 'self.pass_test'.
        It evaluates the 'self.test_results' list, and returns the
        outcome of the test, which will fail if only one of the various
        tests fails. And will pass if all of them fail. It also returns
        the evaluation value, which is given by: <positive_results>/<tot_number_of_requests_sent>
        :return: 'self.test_passed', 'self.test_final_evaluation'.
        """
        # Exclude failed tests results (ie: get rid of False values).
        self.test_results = [res for res in self.test_results if res]
        # Check if True values are six (as the number of tests run) to pass the test.
        # The following expression wants to allow flexibility in the evaluation criteria
        # (ie: change top and bottom values).
        if 6 <= len(self.test_results) <= 6:
            self.test_passed = 1
        else:
            self.test_passed = 0
        # Calculate final evaluation mark (float).
        self.test_final_evaluation = len(self.test_results) / 6
        return self.test_passed, self.test_final_evaluation

    # To be replaced with Machine Learning prediction
    def pass_test(self) -> tuple[int, float]:
        """
        9th to be called. \n
        This method evaluates the results and returns a bool response.
        1 (True), if, from the elaborated data, the communication with the
        web application is considered good enough for the intended
        purpose (in this case Cookie SQL Injection Vulnerability
        Discovery). Otherwise, it will return 0 (False).
        :return: A tuple (test_passed, final_evaluation) from 'self.validate_tests'.
        """
        # Append True or False to the 'self.test_result' list based on varius checks.
        if self.std_deviation < self.std_deviation_threshold:
            self.test_results.append(True)
        else:
            self.test_results.append(False)
        if self.bottom_threshold < self.latency_mean <= self.top_threshold:
            self.test_results.append(True)
        else:
            self.test_results.append(False)
        for k in self.status_codes.keys():
            if k == f"{2}xx":
                self.test_results.append(True)
            else:
                self.test_results.append(False)
        if self.ping_reply:
            self.test_results.append(True)
        else:
            self.test_results.append(False)
        if self.ping_std_deviation < self.ping_std_deviation_threshold:
            self.test_results.append(True)
        else:
            self.test_results.append(False)
        if self.ping_bottom_threshold < self.ping_latency_mean < self.ping_top_threshold:
            self.test_results.append(True)
        else:
            self.test_results.append(False)
        return self.validate_test()

    def _construct_table_record(self, record_type, latencies_list, latency_mean) -> str:
        """
        'self.calculate_std_dev' helper function 6. \n
        :param record_type: GET or ICMP (ping)
        :param latencies_list: The latency list to include in the record
        :param latency_mean: The calculated Latency Mean, either for GET or ICMP
        :return: Record
        """
        record = (
            f"| {record_type} | {max(latencies_list):.3f} | {min(latencies_list):.3f} | {latency_mean} "
            f"| {self.std_deviation} | {self.std_deviation_threshold} | \n")
        return record

    def _set_record_values(self, ping_values) -> tuple[str, float]:
        """
        'self.calculate_std_dev' helper function 5. \n
        :param ping_values: 'ping_values' switch value
        :return: Record Type, Latency Mean
        """
        if ping_values:
            record_type = "**Ping**"
            latency_mean = self.ping_latency_mean
        else:
            record_type = "**GET**"
            latency_mean = self.latency_mean
        return record_type, latency_mean

    def _std_dev_negative_message(self, ping_values) -> tuple[str, str]:
        """
        'self.calculate_std_dev' helper function 4. \n
        :param ping_values: 'ping_values' switch value
        :return: Message, Style
        """
        message = ("[-] GET response time values vary significantly. "
                   "Consider adjusting the Standard Deviation Threshold value.")
        if ping_values:
            message = message.replace(
                "GET", "Ping").replace("Standard", "Ping Standard")
        style = "dark_orange"
        return message, style

    def _std_dev_positive_message(self, ping_values) -> tuple[str, str]:
        """
        'self.calculate_std_dev' helper function 3. \n
        :param ping_values: 'ping_values' switch value
        :return: Message, Style
        """
        message = f"[+] GET responses latency Standard Deviation values are relatively consistent."
        if ping_values:
            message = message.replace(
                "GET", "Ping")
        style = "green"
        return message, style

    def _get_dev_and_dev_thresh(self, ping_values) -> tuple[float, float]:
        """
        'self.calculate_std_dev' helper function 2. \n
        :param ping_values: 'ping_values' switch value
        :return: Standard Deviation and Standard Deviation Threshold
        """
        if ping_values:
            std_deviation = self.ping_std_deviation
            std_deviation_threshold = self.ping_std_deviation_threshold
        else:
            std_deviation = self.std_deviation
            std_deviation_threshold = self.std_deviation_threshold
        return std_deviation, std_deviation_threshold

    def _calculate_std_dev(self, latencies_list, ping_values) -> None:
        """
        'self.calculate_std_dev' helper function 1. \n
        :param latencies_list: the list with the latencies of which to calculate std dev.
        :param ping_values: 'ping_values' switch value
        :return: None
        """
        try:
            if ping_values:
                self.ping_std_deviation = statistics.stdev(latencies_list)
            else:
                self.std_deviation = statistics.stdev(latencies_list)
        except statistics.StatisticsError as e:
            error_message = f"Unable to test latency consistency: {e}"
            raise CheckLatencyConsistencyError(error_message) from e
        else:
            return

    def calculate_std_dev(self, latencies_list, ping_values=False) -> str:
        """
        8th to be called. \n
        It uses the statistics library to calculate the standard deviation,
        which is how much a value gets distant from the average. It may be
        valuable information to understand if the web application's responses
        are received with fluidity, or they arrive to us irregularly, which
        might indicate problems with the web app, or the network.
        :return: 'self.result_tab'.
        """
        # Calculate the standard deviation and set appropriate variable based
        # on 'ping_values' switch.
        self._calculate_std_dev(latencies_list, ping_values)
        # Set appropriate variables for checking against appropriate threshold based on 'ping_values' switch.
        std_deviation, std_deviation_threshold = self._get_dev_and_dev_thresh(ping_values)
        # Check if the standard deviation is below the threshold, and set values to
        # create table record (used for verbosity).
        if std_deviation < std_deviation_threshold:
            message, style = self._std_dev_positive_message(ping_values)
        else:
            message, style = self._std_dev_negative_message(ping_values)
        # Set record's values.
        record_type, latency_mean = self._set_record_values(ping_values)
        if self.verbose:
            self.c.print("\n", message, style=style)
        # Construct table record.
        record = self._construct_table_record(record_type, latencies_list, latency_mean)
        # Update Result Table
        self.result_tab += record
        return self.result_tab

    def _update_response_latency_status_table(self, latency_mean, threshold, response_latency_status_table) -> str:
        """
        'self.get_response_latency_status' helper function 5. \n
        :param latency_mean: Calculated latency mean
        :param threshold: Threshold
        :param response_latency_status_table: Response Latency Status Table
        :return: Response Latency Status Table
        """
        record = f"| {latency_mean} | {threshold} | \n"
        response_latency_status_table += record
        return response_latency_status_table

    def _mean_positive_response(self, ping_values) -> str:
        """
        'self.get_response_latency_status' helper function 4. \n
        :param ping_values: 'ping_values' switch value
        :return: Positive Communication quality status message
        """
        message = (
            f"[+] Web application response is normal. "
        )
        if ping_values:
            message = message.replace("Web application response is", "Network conditions are")
        return message

    def _mean_negative_response(self, ping_values) -> str:
        """
        'self.get_response_latency_status' helper function 3. \n
        :param ping_values: 'ping_values' switch value
        :return: Negative Communication quality status message
        """
        message = (
            f"[-] Web application response is a bit slow. "
            f"You might want to consider increasing the quality threshold value. \n"
        )
        if ping_values:
            message = message.replace(
                "Web application response", "Network"
            ).replace(
                "quality", "ping"
            )
            # message = message.replace("quality", "ping")
        return message

    def _handle_request_by_type(self, bottom_threshold, top_threshold, ping_values) -> str:
        """
        'self.get_response_latency_status' helper function 2. \n
        :param bottom_threshold: Bottom threshold value from 'self._get_threshold_frame'
        :param top_threshold: Top threshold value from 'self._get_threshold_frame'
        :param ping_values: 'ping_values' switch value
        :return: Response Latency Status Table
        """
        if ping_values:
            self.ping_bottom_threshold = bottom_threshold
            self.ping_top_threshold = top_threshold
            response_latency_status_table = self.ping_response_latency_status_tab
        else:
            self.bottom_threshold = bottom_threshold
            self.top_threshold = top_threshold
            response_latency_status_table = self.response_latency_status_tab
        return response_latency_status_table

    def _get_threshold_frame(self, latency_mean, threshold) -> tuple[float, float]:
        """
        'self.get_response_latency_status' helper function 1. \n
        :param latency_mean:
        :param threshold:
        :return: Top and Bottom Thresholds values
        """
        bottom_threshold = latency_mean - threshold
        top_threshold = latency_mean + threshold
        return bottom_threshold, top_threshold

    def get_response_latency_status(self, latency_mean, threshold, ping_values=False) -> str:
        """
        7th to be called. \n
        It parses top and bottom threshold value from 'self.threshold', which represents
        the delta (+/-), that is the lowest and the highest values the response time
        must be within, in order to be considered a normal response time.
        :return: 'self.response_latency_status_table': | Average Response Time | Current Threshold Value |.
        """
        # Calculate bottom and top threshold
        bottom_threshold, top_threshold = self._get_threshold_frame(latency_mean, threshold)
        # Set variables based on 'ping_values' flag, and sets the appropriate output table
        # for verbosity (allows to print a rich Markdown table)
        response_latency_status_table = self._handle_request_by_type(bottom_threshold, top_threshold, ping_values)
        # Check that latency mean inside specified threshold values, and prints
        # appropriate message when verbose.
        if not bottom_threshold < latency_mean <= top_threshold:
            message = self._mean_negative_response(ping_values)
            if self.verbose:
                self.c.print(Markdown(message), style="dark_orange")
        else:
            message = self._mean_positive_response(ping_values)
            if self.verbose:
                self.c.print(Markdown(message), style="green")
        # Create table record, append it and return table based on 'ping_values' switch.
        response_latency_status_table = self._update_response_latency_status_table(
            latency_mean, threshold, response_latency_status_table
        )
        return response_latency_status_table

    def _handle_mean_error_messages(self, e, ping_values) -> str:
        """
        'self.process_latency_mean' helper function 2. \n
        :param e: Error message from exception
        :param ping_values: 'ping_value' switch value
        :return:
        """
        if ping_values:
            error_message = f"Unable to calculate ping responses times mean for url '{self.url}': {e}"
        else:
            error_message = f"Unable to calculate GET responses times mean for url '{self.url}': {e}"
        return error_message

    def _calculate_mean(self, latencies_list, ping_values) -> float:
        """
        'self.process_latency_mean' helper function 1. \n
        :param latencies_list: The list of latencies of which to calculate the mean.
        :param ping_values:
        :return:
        """
        if ping_values:
            self.ping_latency_mean = statistics.mean(latencies_list)
            return self.ping_latency_mean
        else:
            self.latency_mean = statistics.mean(latencies_list)
            return self.latency_mean

    def process_latency_mean(self, latencies_list, ping_values=False) -> float | Decimal | Fraction:
        """
        6th to be called. \n
        It calculates the mean between all the time values appended from the '\\@timer'
        decorator. These are the runtimes of the 'self._assess_url' method, essentially
        the response times to our GET requests.
        :return: 'self.latency_mean'. The mean of the time values in 'self.latencies_list'.
        """
        try:
            # Calculate mean and assign its value to a different variable
            # based on the 'ping_values' switch.
            return self._calculate_mean(latencies_list, ping_values)
        except statistics.StatisticsError as e:
            error_message = self._handle_mean_error_messages(e, ping_values)
            self.c.print(error_message, style="yellow3")
            sys.exit(1)

    def _get_response(self, response) -> str:
        """
        'self.process_status_codes' helper function 1. \n
        :param response: The future you need the response from
        :return:
        """
        try:
            # Parse status code.
            status_code = response.status_code
        except AttributeError as e:
            self.c.print(
                f"Could not process status code for URL: '{self.url}': {e} \nSkipping..",
                style="dark_orange"
            )
            pass
        else:
            # Parse and return the status code id.
            status_code_id = f"{str(status_code)[0]}xx"
            return status_code_id

    def process_status_codes(self) -> dict:
        """
        5th to be called. \n
        This method iterates through the response dictionaries in the 'self.responses_list',
        where all the futures are stored under their 'request id'. It extracts the response
        status code from each of them. It creates a dictionary with the found
        response codes as keys, and a list with each found response of that code.
        :return: 'self.status_codes': dict of received responses status codes.
        """
        # Iterate through the responses list dictionaries.
        for req_dict in self.responses_list:
            for request_id, future in req_dict.items():
                # Parse the response from the future
                response: requests.Response = future.result()
                # Parse the status code id and append the response to the list of
                # the corresponding status code category.
                status_code_id = self._get_response(response)
                if status_code_id:
                    self.status_codes[status_code_id].append([response, self.url])
        return self.status_codes

    def _handle_ping_exceptions(self) -> None:
        """
        'self.ping_test' helper function 1. \n
        :return: None
        """
        if self.ping_reply is None:
            self.ping_reply = 0.0
        if self.ping_reply is False:
            self.ping_reply = 0.0

    def ping_test(self) -> float:
        """
        4th to be called. \n
        This method pings the host's IP address and stores the response time in
        'self.ping_reply'. Then it checks if timed out (None) or it failed (False).
        :return: Ping response time (ms).
        """
        self.ping_reply = ping(self.host)
        self._handle_ping_exceptions()
        self.ping_latencies_list.append(self.ping_reply)
        return self.ping_reply

    @timer
    def _assess_url(self) -> requests.Response:
        """
        3rd to be called. \n
        It's a helper of the 'self.assess_url()' method.
        It takes care of sending a GET requests to the 'self.url' URL and store its response
        in the 'self.response' variable. The '@timer' decorator takes care of the response times.
        :return: 'self.response'
        """
        try:
            # Send the GET request and save the response.
            self.response = requests.get(self.url)
        except requests.exceptions.RequestException as e:
            error_message = f"Request failed: {e}"
            self.c.print(error_message)
        else:
            return self.response

    def _acquire_ping_response_data(self, scan_id) -> None:
        """
        'self.assess_url' helper function 5. \n
        :param scan_id: The order number of the scan
        :return: None
        """
        self.ping_responses_list.append({f"PingRequestId_{scan_id}": self.ping_future})
        # List of futures for threads handling.
        self.futures.append(self.ping_future)

    def _acquire_get_response_data(self, scan_id) -> None:
        """
        'self.assess_url' helper function 4. \n
        :param scan_id: The order number of the scan
        :return: None
        """
        self.responses_list.append({f"RequestId_{scan_id}": self.future})
        # Create a list of futures for handling threads, for example killing
        # them on closure (see 'self.close').
        self.futures.append(self.future)

    def _delay(self) -> None:
        """
        'self.assess_url' helper function 3. \n
        :return: None
        """
        if self.delay:
            time.sleep(self.delay)

    def _create_futures(self) -> None:
        """
        'self.assess_url' helper function 2. \n
        :return: None
        """
        self.future = self.executor.submit(self._assess_url)
        self.ping_future = self.executor.submit(self.ping_test)

    def _check_future_state(self) -> None:
        """
        'self.assess_url' helper function 1. \n
        :return:
        """
        if self.future:
            if self.future.cancelled():
                error_message = f"Future status cancelled: {self.future.cancelled()}"
                self.close(error_message)

    def assess_url(self) -> tuple[list[dict], list[dict]]:
        """
        2nd to be called.\n
        This method creates a list of dictionaries, with request ids as keys and
        the response to the GET request as values. It does so by means of the
        'self._assess_url()' helper method, which actually takes care of sending
        the requests and storing the responses in the 'self.response' instance variable.\n
        Note: 'self.accuracy' is the number of requests over which the assessment will be taken.
        :return: 'self.responses_list' -> [{"RequestId": requests.Response}]
        """
        try:
            with Lock():
                # Start ThreadPoolExecutor to send concurrent GET and ping requests
                with ThreadPoolExecutor(max_workers=self.accuracy) as self.executor:
                    for thread_id, queue in enumerate(self.queues):
                        while not queue.empty():
                            # Check if future is in a 'cancelled' state. That would typically indicate
                            # a KeyboardInterrupt. If so kill all other processes and shutdown the executor.
                            self._check_future_state()
                            # Create futures for both GET and ping requests
                            self._create_futures()
                            # If specified, apply the delay, the send frequency of the requests.
                            self._delay()
                            # Pull resource from working queue.
                            scan_id = self.queues[thread_id].get()
                            # Populate a list of dictionaries with the responses from each GET scan
                            # and a list of futures for threads handling.
                            self._acquire_get_response_data(scan_id)
                            # Same for pings.
                            # Populate list of dictionaries with the responses from each ICMP scan
                            # and a list of futures for threads handling.
                            self._acquire_ping_response_data(scan_id)
                return self.responses_list, self.ping_responses_list
        except KeyboardInterrupt:
            self.close("Detected CTRL+C. Bye.", keyboard_interrupt=True)

    def create_queues(self) -> None:
        """
        1st to be called. \n
        This method is responsible for populating the 'self.queues' list. It does so by
        enumerating the 'range(self.accuracy)' range, and evenly distributing resources,
        in this case the 'scan_id' ('self.accuracy' is actually the number of scans that
        will be performed, ie: the number of requests sent), among the queues in the
        'self.queues' list. To evenly distribute the resources it uses a basic form of
        round-robin distribution with the modulo operator.
        :return: None.
        """
        for i, scan_id in enumerate(range(self.accuracy)):
            # The thread_id will keep cycling through the queues accessing the 'self.queues'
            # list by index from 0 to accuracy. In this manner each thread will have its
            # assigned queue to get resources from, without the thread being able to overlap
            # themselves.
            thread_id = i % self.accuracy
            self.queues[thread_id].put(scan_id)

    def run(self) -> tuple[Table, bool, np.ndarray]:
        """
        Root Method. \n
        This is the central method, the one that calls, in order, all the other
        methods, so for the class to run. It returns a tuple with the data
        from the analysis in a rich Table, and the values related to the
        test, if passed or not, and the AI prediction, as a bool and str.
        :return: Final Result Table ('self.final_table'), Test Passed ('self.test_passed')
        and Ai Prediction ('self.ai_prediction').
        """
        self.create_queues()
        try:
            # Send the GET requests using ThreadPoolExecutor.
            self.assess_url()
        except AssessURLRequestError as e:
            error_message = f"[-] AssessURL Run Error: {e}"
            self.c.print(error_message)
            pass
        self.process_status_codes()
        # Calculate latency mean for GET request.
        self.process_latency_mean(self.latencies_list)
        # Calculate latency mean for ICMP (ping) request.
        self.process_latency_mean(self.ping_latencies_list, ping_values=True)
        # Compare means with threshold values.
        self.get_response_latency_status(self.latency_mean, self.threshold)
        self.get_response_latency_status(self.ping_latency_mean, self.ping_threshold, ping_values=True)
        try:
            # Calculate Standard Deviations for both GET and ping latencies values.
            self.calculate_std_dev(self.latencies_list)
            self.calculate_std_dev(
                self.ping_latencies_list, ping_values=True)
        except CheckLatencyConsistencyError as e:
            error_message = f"[-] AssessUrl Run Error: {e}.\n* Hint: Accuracy option ('-a') must be greater than 1."
            self.c.print(error_message)
        else:
            # Elaborate the results of the analysis and pass/fail the test.
            self.pass_test()
            # Generate a report with the data from the analysis.
            self.generate_report()
            # Write analysis data to CSV file ('--outfile')
            self.write_csv_file()
            # Parse the AI model's prediction of the test's outcome.
            self.ai_prediction = self.ai_confirm()
            # Initialize the 'self.status_codes' dictionary to eliminate garbage collection.
            self.status_codes = {}
            # Return final results.
            return self.final_table, self.test_passed, self.ai_prediction

    def kill_all_threads(self) -> None:
        """
        Closing Help Method. \n
        This method kills each running future in 'self.future'.
        :return: None
        """
        for future in self.futures:
            future.cancel()

    def close(self, error_message=None, keyboard_interrupt=False) -> None:
        """
        Closing method. \n
        It prints the error message passed as an argument,
        then the advice to check out --help.
        Finally, exits the program.
        :param keyboard_interrupt:
        :param error_message: error message passed in when error raised
        :return: None. Exit messages & Exit.
        """
        self.kill_all_threads()
        self.executor.shutdown()
        if not keyboard_interrupt:
            self.c.print(Markdown(error_message), style="red")
            self.c.print("\n", Markdown("Use --help for more information or read the README.md file."))
        sys.exit(0)


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
    default=0.1,
    show_default=True,
    required=True,
    type=float
)
@click.option(
    "-y", "--ping-std-deviation-threshold", "ping_std_deviation_threshold",
    help="The value over which the ping standard deviation should not go beyond"
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
    "-o", "--outfile",
    help="Specify a path where you want to save a csv with all data to.",
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
def main(
        url: str, accuracy, threshold, ping_threshold, std_deviation_threshold,
        ping_std_deviation_threshold, delay, outfile, verbose: bool
):
    latency_assessor = AssessLatency(
        url, accuracy, threshold, ping_threshold, std_deviation_threshold,
        ping_std_deviation_threshold, delay, outfile, verbose=verbose
    )
    test_passed = latency_assessor.run()
    return test_passed


if __name__ == '__main__':
    main()
