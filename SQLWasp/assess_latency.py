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
from threading import Lock
from urllib.parse import urlparse

import click
import pandas as pd
import requests
from ping3 import ping
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from SQLWasp.custom_errors import CheckLatencyConsistencyError, AssessURLRequestError
from SQLWasp.ai import AIControl
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
    def __init__(self, url: str, accuracy: int = 10, threshold: float = 0.1, ping_threshold: float = 0.1,
                 std_deviation_threshold: float = 0.1, ping_std_deviation_threshold: float = 0.1, delay: float = 0.0,
                 outfile: Path | str = None, verbose: bool = False) -> None:
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
        self.host = socket.gethostbyname(
            urlparse(self.url).hostname)
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
        self.latency_average = 0.0
        self.ping_latency_average = 0.0
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

    def ai_confirm(self):
        ai = AIControl(self.trained_ai_model_path, self.input_data_csv_path, self.outfile)
        ai.run()
        return ai.predictions
        # return f"AI Confirmation Test: {AI.predictions}"
        # self.c.print(f"AI Confirmation Test:", AI.predictions, style="cyan")
        # ai.train_model()

    def _create_pandaz_table(self):
        table_data = [
            ["GET Sent", self.accuracy],
            ["Ping Sent", self.accuracy],
            ["Delay", self.delay],
            ["Threshold", self.threshold],
            ["Ping Threshold", self.ping_threshold],
            ["Std Dev Threshold", self.std_deviation_threshold],
            ["Ping Std Dev Threshold", self.ping_std_deviation_threshold],
            ["GET Latency Average", self.latency_average],
            ["Min GET Latency", min(self.latencies_list)],
            ["Max GET Latency", max(self.latencies_list)],
            ["Ping Latency Average", self.ping_latency_average],
            ["Min Ping Latency", min(self.ping_latencies_list)],
            ["Max Ping Latency", max(self.ping_latencies_list)],
            ["Std Dev", self.std_deviation],
            ["Ping Std Dev", self.ping_std_deviation],
        ]
        # self.c.print(self.status_codes)
        for status_code_category, response in self.status_codes.items():
            table_data.append(
                [f"{status_code_category}", len(response)]
            )
        self.clear_status_codes()
        table_data.append(["Test Final Evaluation", self.test_final_evaluation])
        table_data.append(["Test Passed", self.test_passed])
        # self.c.print(table_data)
        return table_data

    def pandaz(self):
        # self.c.print(Markdown(f"# Table Data \n"))
        table_data = self._create_pandaz_table()
        table_dict = [dict(table_data)]
        df = pd.DataFrame(table_dict)
        # self.c.print(df)
        return df

    def write_csv_file(self):
        table_data = self.pandaz()
        if os.path.exists(self.outfile):
            table_data.to_csv(self.outfile, mode="a", index=False, header=False)
        else:
            table_data.to_csv(self.outfile, index=False)
        table_data.to_csv(self.ai_data_bucket_path, index=False)
        return self.table_data

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
        self.final_table.add_row("URL", str(self.url), style=None)
        self.final_table.add_row("Host", str(self.host), style=None)
        self.final_table.add_row("Number of GET Requests Sent", str(self.accuracy), style=None)
        self.final_table.add_row("Number of Ping Requests Sent", str(self.accuracy), style=None)
        self.final_table.add_row("Requests Delay", f"{self.delay} secs", style=None)
        self.final_table.add_row("Communication Quality Threshold", f"{self.threshold} sec")
        self.final_table.add_row("Ping Threshold", f"{self.ping_threshold} sec")
        self.final_table.add_row("Standard Deviation Threshold", f"{self.std_deviation_threshold} sec")
        self.final_table.add_row("Ping Standard Deviation Threshold", f"{self.ping_std_deviation_threshold} sec")
        self.final_table.add_row("GET Responses Latency Average", f"{self.latency_average} secs")
        self.final_table.add_row("Min GET Responses Latency", f"{min(self.latencies_list)} secs")
        self.final_table.add_row("Max GET Responses Latency", f"{max(self.latencies_list)} secs")
        self.final_table.add_row("Ping responses Latency Average", f"{self.ping_latency_average} secs")
        self.final_table.add_row("Min Ping responses Latency", f"{min(self.ping_latencies_list)} secs")
        self.final_table.add_row("Max Ping responses Latency", f"{max(self.ping_latencies_list)} secs")
        self.final_table.add_row("Standard Deviation", f"{self.std_deviation} secs")
        self.final_table.add_row("Ping Standard Deviation", f"{self.ping_std_deviation} secs")
        for status_code_category, response in self.status_codes.items():
            self.final_table.add_row(
                f"Status Code: {status_code_category}",
                f"Responses received: {str(len(self.status_codes.get(status_code_category)))}"
            )
        self.final_table.add_row("Test Final Evaluation", str(self.test_final_evaluation))
        self.final_table.add_row("Test Passed", str("True" if self.test_passed else "False"), style="blink")
        return self.final_table

    def validate_test(self) -> tuple[int, float]:
        self.test_results = [res for res in self.test_results if res]
        if 6 <= len(self.test_results) <= 6:
            self.test_passed = 1
        else:
            self.test_passed = 0
        self.test_final_evaluation = len(self.test_results) / 6
        return self.test_passed, self.test_final_evaluation

    # To be replaced with Machine Learning prediction
    def network_test_passed(self) -> tuple[int, float]:
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
            self.test_results.append(True)
        else:
            self.test_results.append(False)
        if self.bottom_threshold < self.latency_average <= self.top_threshold:
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
        if self.ping_bottom_threshold < self.ping_latency_average < self.ping_top_threshold:
            self.test_results.append(True)
        else:
            self.test_results.append(False)
        return self.validate_test()

    def check_latency_consistency(self, latencies_list, std_deviation_threshold, ping_values=False) -> str:
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
            if ping_values:
                self.ping_std_deviation = statistics.stdev(latencies_list)
            else:
                self.std_deviation = statistics.stdev(latencies_list)
        except statistics.StatisticsError as e:
            error_message = f"Unable to test latency consistency: {e}"
            raise CheckLatencyConsistencyError(error_message) from e
        # Set a threshold for what you consider "regular"
        # 'self.std_deviation_threshold' = 0.1 (or whatever)  # You can adjust this value based on your specific needs
        # Check if the standard deviation is below the threshold
        else:
            if ping_values:
                std_deviation = self.ping_std_deviation
                std_deviation_threshold = self.ping_std_deviation_threshold
            else:
                std_deviation = self.std_deviation
                std_deviation_threshold = self.std_deviation_threshold
            if std_deviation < std_deviation_threshold:
                message = f"[+] GET responses latency Standard Deviation values are relatively consistent."
                if ping_values:
                    message = message.replace(
                        "GET", "Ping")
                style = "green"
            else:
                message = ("[-] GET response time values vary significantly. "
                           "Consider adjusting the Standard Deviation Threshold value.")
                if ping_values:
                    message = message.replace(
                        "GET", "Ping").replace("Standard", "Ping Standard")
                style = "dark_orange"
            if ping_values:
                record_type = "**Ping**"
                latency_average = self.ping_latency_average
            else:
                record_type = "**GET**"
                latency_average = self.latency_average

            if self.verbose:
                self.c.print("\n", message, style=style)

            record = (
                f"| {record_type} | {max(latencies_list):.3f} | {min(latencies_list):.3f} | {latency_average} "
                f"| {self.std_deviation} | {self.std_deviation_threshold} | \n")
            self.result_tab += record
            return self.result_tab

    def get_response_latency_status(self, latency_average, threshold, ping_values=False) -> str:
        """
        5th to be called. \n
        It parses top and bottom threshold value from 'self.threshold', which
        represents the delta (+/-), the lowest and the highest values, the
        response time must be within, in order to be considered a normal response
        time.
        :return: 'self.response_latency_status_tab': | Average Response Time | Current Threshold Value |.
        """
        bottom_threshold = latency_average - threshold
        top_threshold = latency_average + threshold
        if ping_values:
            self.ping_bottom_threshold = bottom_threshold
            self.ping_top_threshold = top_threshold
            response_latency_status_table = self.ping_response_latency_status_tab
        else:
            self.bottom_threshold = bottom_threshold
            self.top_threshold = top_threshold
            response_latency_status_table = self.response_latency_status_tab
        if not bottom_threshold < latency_average <= top_threshold:
            message = (
                f"[-] Web application response is a bit slow. "
                f"You might want to consider increasing the quality threshold value. \n"
            )
            if ping_values:
                message = message.replace("Web application response", "Network")
                message = message.replace("quality", "ping")
            if self.verbose:
                self.c.print(Markdown(message), style="dark_orange")
        else:
            message = (
                f"[+] Web application response is normal. "
            )
            if ping_values:
                message = message.replace("Web application response is", "Network conditions are")
            if self.verbose:
                self.c.print(Markdown(message), style="green")
        record = f"| {latency_average} | {threshold} | \n"
        response_latency_status_table += record
        return response_latency_status_table

    def process_latency_average(self, latencies_list, ping_values=False) -> float | Decimal | Fraction:
        """
        4th to be called. \n
        It calculates the mean between all the
        time values appended from the '\\@timer' decorator. These are the runtimes
        of the 'self._assess_url' method, essentially the response times to our
        GET requests:
        :return: 'self.latency_average'. The mean of the time values in 'self.latencies_list'.
        """
        if ping_values:
            self.ping_latency_average = statistics.mean(latencies_list)
            # self.c.print(f"Ping Latency Average {self.ping_latency_average}")
            return self.ping_latency_average
        else:
            self.latency_average = statistics.mean(latencies_list)
            # self.c.print(f"Latency Average {self.latency_average}")
            return self.latency_average

    def clear_status_codes(self):
        for status_code_category in self.status_codes.keys():
            self.status_codes[status_code_category] = []
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
            # self.c.print(self.responses_list, style="red")
            for request_id, future in req_dict.items():
                # self.c.print(f"{request_id}: {future}")
                response: requests.Response = future.result()
                try:
                    status_code = response.status_code
                except AttributeError as e:
                    self.c.print(f"Could not process status code: {e} \nSkipping..", style="dark_orange")
                    pass
                else:
                    status_code_id = f"{str(status_code)[0]}xx"
                    self.status_codes[status_code_id].append([response, self.url])
            self.responses_list = []
        return self.status_codes

    def ping_test(self, icmp_req_id):
        self.ping_reply = ping(self.host)
        if self.ping_reply is None:
            self.ping_reply = 0.0
        if self.ping_reply is False:
            self.ping_reply = 0.0
        self.ping_latencies_list.append(self.ping_reply)
        return self.ping_reply

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
            self.c.print(error_message)
            # self.close(error_message)
        else:
            # self.c.print(f"Response {req_id}: {self.response}")
            return self.response

    def assess_url(self) -> tuple[list[dict], list[dict]]:
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
            with Lock():
                with ThreadPoolExecutor(max_workers=self.accuracy) as self.executor:
                    for req_id, scan in enumerate(range(self.accuracy)):
                        if self.future:
                            if self.future.cancelled():
                                error_message = f"Future status cancelled: {self.future.cancelled()}"
                                self.close(error_message)

                        self.future = self.executor.submit(self._assess_url, req_id)
                        self.ping_future = self.executor.submit(self.ping_test, req_id)
                        if self.delay:
                            time.sleep(self.delay)
                        self.responses_list.append({f"RequestId_{req_id}": self.future})
                        self.futures.append(self.future)
                        self.ping_responses_list.append({f"PingRequestId_{req_id}": self.ping_future})
                        self.futures.append(self.ping_future)
                        # self.c.print(f"Sent GET request {req_id}. Ping request {req_id}")
                return self.responses_list, self.ping_responses_list
        except KeyboardInterrupt:
            self.close("Detected CTRL+C. Bye.", keyb_int=True)

    def run(self) -> tuple[Table, bool, str]:
        """
        Method 0 \n
        This is the central method, the one that calls , in order, all the other
        required methods, so for the class to initialize and run.
        :return: None
        """
        # Send the GET requests using ThreadPoolExecutor
        try:
            self.assess_url()
            # self.c.print([(list(d.keys())[0], list(d.values())[0].result()) for d in self.responses_list])
            # self.c.print([(list(d.keys())[0], list(d.values())[0].result()) for d in self.ping_responses_list])
        except AssessURLRequestError as e:
            error_message = f"[-] AssessURL Run Error: {e}"
            self.c.print(error_message)
            pass
        self.process_status_codes()
        self.process_latency_average(self.latencies_list)
        self.process_latency_average(self.ping_latencies_list, ping_values=True)
        self.get_response_latency_status(self.latency_average, self.threshold)
        self.get_response_latency_status(self.ping_latency_average, self.ping_threshold, ping_values=True)
        # self.c.print(Markdown(self.get_response_latency_status(self.latency_average, self.threshold)))
        # self.c.print(
        #     Markdown(
        #         self.get_response_latency_status(self.ping_latency_average, self.ping_threshold, ping_values=True)
        #     )
        # )
        try:
            # self.c.print(Markdown(self.check_latency_consistency(self.latencies_list, self.std_deviation_threshold)))
            self.check_latency_consistency(self.latencies_list, self.std_deviation_threshold)
            self.check_latency_consistency(
                self.ping_latencies_list, self.ping_std_deviation_threshold, ping_values=True)
            # self.c.print(
            #     Markdown(
            #         self.check_latency_consistency(
            #             self.ping_latencies_list, self.ping_std_deviation_threshold, ping_values=True
            #         )
            #     )
            # )
        except CheckLatencyConsistencyError as e:
            error_message = f"[-] AssessUrl Run Error: {e}.\n* Hint: Accuracy option ('-a') must be greater than 1."
            self.c.print(error_message)
            # self.close(error_message)
        else:
            # self.ping_test()
            self.network_test_passed()
            # self.c.print(f"Test Passed: {self.network_test_passed()} \n", style="green4")
            self.generate_report()
            # self.c.print(f"Generating report. \n", self.generate_report())
            if self.outfile:
                # self.c.print(f"[i] Writing outfile.")
                self.write_csv_file()
                self.ai_prediction = self.ai_confirm()
                prediction_is_valid = self.test_passed == self.ai_prediction[0]
                if prediction_is_valid:
                    pass
                    # self.prediction_validation_list.append(prediction_is_valid)
                    # self.c.print(Markdown(f"Prediction is valid: \n* {prediction_is_valid}"), style="red")
                # self.c.print(self.final_table, "\n", Markdown(f"Prediction is valid: \n* {prediction_is_valid}"))
            self.status_codes = {}
            # self.close(end_of_run=True)
            return self.final_table, self.test_passed, self.ai_prediction

    def kill_all_threads(self):
        for future in self.futures:
            future.cancel()

    def close(self, error_message=None, keyb_int=False, end_of_run=False) -> None:
        """
        Closing method. \n
        It prints the error message passed as an argument,
        then the advice to check out --help.
        Finally, exits the program.
        :param keyb_int:
        :param error_message: error message passed in when error raised
        :return: None. Exit messages & Exit.
        """
        self.kill_all_threads()
        self.executor.shutdown()
        if not keyb_int:
            self.c.print(Markdown(error_message), style="red")
            self.c.print("\n", Markdown("Use --help for more information or read the README.md file."))
        if not end_of_run:
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
    lat_ass = AssessLatency(
        url, accuracy, threshold, ping_threshold, std_deviation_threshold,
        ping_std_deviation_threshold, delay, outfile, verbose=verbose
    )
    test_passed = lat_ass.run()
    # responses_list = lat_ass.responses_list
    return test_passed


if __name__ == '__main__':
    main()
