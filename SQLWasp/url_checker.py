#!/usr/bin/env python3.12
# url_checker.py

import csv
import json
import logging
import sys

import click
import requests
from rich.console import Console
from rich.markdown import Markdown

from SQLWasp.custom_errors import InvalidURLError, InvalidInputListError
from SQLWasp.reverse_logger import (
    ReverseLogger,
    log_error_and_raise_exception,
    filename_parser,
)
from data.input.data_sources import (
    full_table_data,
    validation_result_tab,
    check_result_tab,
    urls_to_check_tuple,
)

OUTPUT_FILE_PATH = "data/output/check_url_out.csv"

filename, log_filepath = filename_parser(log_file_name=__file__)
rev_log = ReverseLogger(
    logger_name=filename,
    log_file_path=log_filepath,
    logging_level=logging.DEBUG,
    encoding="utf-8",
)


class UrlChecker:
    """
    UrlChecker checks URL format, captures HEAD and GET requests.
    """

    def __init__(
        self,
        urls: tuple[str] = None,
        url_list: list = None,
        outfile: bool = False,
        validation_result_table: str = validation_result_tab,
        check_result_table: str = check_result_tab,
    ) -> None:
        """
        Initialize the UrlChecker instance.

        :param urls: Tuple of URLs.
        :param url_list: List of URLs.
        :param outfile: Flag indicating whether to write to an output file.
        :param validation_result_table: Table for validation results.
        :param check_result_table: Table for check results.
        """
        self.outfile: bool = outfile
        self.c: Console = Console()
        self.data_table: list = full_table_data
        self.url: str = ""
        self.url_list: list = url_list
        self.urls: tuple = urls
        self.validation_output_report: list | tuple = []
        self.head_request_output_report: list | tuple = []
        self.get_request_output_report: list | tuple = []
        self.valid_url_records: list = []
        self.invalid_url_records: list = []
        self.response: requests.Response = requests.Response()
        self.status_record: str = ""
        self.group: str = ""
        # self.status_record_str: str = ""
        self.validation_result_table_default: str = validation_result_table
        self.check_result_table_default: str = check_result_table
        self.validation_result_table: str = validation_result_table
        self.check_result_table: str = check_result_table
        self.url_is_valid: None = None
        self.sending_get_request: bool = False
        self.sending_head_request = False

    def partial_init(self):
        self.validation_output_report: list | tuple = []
        self.head_request_output_report: list | tuple = []
        self.get_request_output_report: list | tuple = []
        self.valid_url_records: list = []
        self.invalid_url_records: list = []
        self.response: requests.Response = requests.Response()
        self.status_record: str = ""
        self.group: str = ""
        self.validation_result_table: str = self.validation_result_table_default
        self.url_is_valid: None = None
        self.sending_get_request: bool = False
        self.sending_head_request = False

    # ################################### START OF VALIDATION PROCESS ################################### #

    def _load_json_dumps(self) -> None:
        """
        Processes JSON strings passed in with the -l option in correct JSON syntax.
        This is because the app accepts a python list as commend line argument "-l" option.\n
        Raises InvalidInputListError if the argument is not a list type.
        :return: None
        """
        try:
            list(json.dumps(self.url_list))
        except TypeError as e:
            error_message = (
                f"Type '{type(self.url_list)}' not allowed {e}."
                f"""Enter a list in JSON syntax (i.e.: '["url_1", "url_2"]')"""
            )
            log_error_and_raise_exception(
                rev_log, error_message, InvalidInputListError(error_message)
            )

    def _validate_url_list_type(self) -> None:
        """
        Checks if the URL List is actually a list type, else raises InvalidInputListError
        :return:
        """
        if not isinstance(self.url_list, list):
            error_message = (
                f"Type '{type(self.url_list)}' not allowed. "
                f"""Enter a list in JSON syntax (i.e.: '["url_1", "url_2"]')"""
            )
            log_error_and_raise_exception(
                rev_log, error_message, InvalidInputListError(error_message)
            )

    def _validate_input_type(self) -> None:
        """
        If there is a self.url_list (click option), checks if it's a list type, as the app takes "json.loads" input.
        :return: None
        """
        # Load json.dumps and validate URL type is List
        self._load_json_dumps()
        # Check if URL List is a list type
        self._validate_url_list_type()

    def elaborate_cmd_line_args(self) -> None:
        """
        These are URLs passed via click positional ARGUMENT, no option i.e.: "-c" or similar.
        Appending each URL in the iterable in the self.url_list.
        :return: None
        """
        if self.urls:
            # Append all positional arg URL to self.url_list
            for url in self.urls:
                self.url_list.append(url)

    def process_urls(self) -> None:
        """
        Processes command line arguments and options. Initiates class variables and URLs lists.
        :return: None
        """
        # If there is a URL List "self.url_list" (click option),
        # checks if it's a list type, as the app takes json.loads input.
        if self.url_list is not None:
            self._validate_input_type()
        else:
            self.url_list = []
            # These are URLs passed via click positional ARGUMENT, no option i.e.: "-c" or similar.
            # Appending each URL in the iterable in the self.url_list
            self.elaborate_cmd_line_args()

    def check_url_format(self) -> bool | Exception:
        """
        Checks if the syntax of the URL is correct using "validators". \n
        If the URL is not valid it raises an InvalidURLError.
        :return: True | InvalidURLError
        """
        import validators

        if not validators.url(self.url):
            error_message = self.url
            self.url_is_valid = validators.url(self.url)
            log_error_and_raise_exception(
                logger_obj=rev_log,
                error_message=error_message,
                exception=InvalidURLError(error_message),
            )
        else:
            return True

    def validate(self) -> None:
        """
        Validates the structure of the URL and populates the Validation Output Report
         appending both True and False results. It also updates the Validation Result Table.
        :return: None.
        """
        try:
            self.url_is_valid = self.check_url_format()
        except InvalidURLError as e:
            # Update Validation Result Table with string.
            message = (
                f"| Error validating the URL | {e} | {self.url_is_valid is True} | \n"
            )
            self.validation_result_table += message
            # Update Validation Output Report with tuple.
            stripped_message = tuple(message.split("|")[1:-1:1])
            self.validation_output_report.append(stripped_message)
        else:
            # Update Validation Result Table with string.
            message = f"| Validation succeeded | {self.url} | {self.url_is_valid} | \n"
            self.validation_result_table += message
            # Update Validation Output Report with tuple.
            stripped_message = tuple(message.split("|")[1:-1:1])
            self.validation_output_report.append(stripped_message)

    def _write_out_file_init_data(self, check_url_data):
        open_mode = "w"
        column_raw = (
            "Outcome",
            "URL",
            "Validation Passed",
        )
        if check_url_data:
            open_mode = "a"
            column_raw = (
                "Status",
                "URL",
                "Category",
                "Description",
            )
        outfile_name = OUTPUT_FILE_PATH
        return open_mode, column_raw, outfile_name

    def parse_output_report(self, check_url_data):
        output_report = self.validation_output_report
        if check_url_data:
            if self.sending_head_request:
                output_report = self.head_request_output_report
            if self.sending_get_request:
                output_report = self.get_request_output_report
        return output_report

    def write_main_file_body(self, writer, record, check_url_data):
        if check_url_data:
            try:
                # Only write to file records which have a status code at the first column
                if isinstance(int(record[0].split()[0]), int):
                    writer.writerow(record)
            except ValueError:
                pass
        else:
            writer.writerow(record)

    def _parse_req_type_print_confirm_message(self, outfile_name):
        if self.sending_get_request:
            self.c.print(f"Created GET requests outfile '{outfile_name}'.")
            return
        elif self.sending_head_request:
            self.c.print(f"Created HEAD requests outfile '{outfile_name}'.")
            return

    def _print_validation_confirm_message(self, outfile_name):
        if self.sending_head_request or self.sending_get_request:
            return
        else:
            self.c.print(f"Created URL validation outfile '{outfile_name}'.")

    def _write_outfile_final_message(
        self, check_url_data: bool, outfile_name: str
    ) -> None:
        """
        Prints the final confirmation message after the outputfile has been written.
        :param check_url_data: If True it means the actual sending of HEAD or GET requests has been set
        (not just validating the URL format).
        :param outfile_name: This is the path of the output file
        :return:
        """
        if check_url_data:
            self._parse_req_type_print_confirm_message(outfile_name)
        else:
            self._print_validation_confirm_message(outfile_name)

    def _write_csv_file(self, outfile_name, open_mode, column_raw, check_url_data):
        with open(outfile_name, open_mode, encoding="utf-8") as outfile:
            writer = csv.writer(outfile, delimiter=",")
            writer.writerow(column_raw)
            # Parse output report based on what table will be written to file: Validation, HEAD or GET Output Report
            output_report = self.parse_output_report(check_url_data)
            # Iterate report, write main body (a raw) to file then leave a blank raw.
            for record in output_report:
                self.write_main_file_body(writer, record, check_url_data)
            writer.writerow([])

    def write_outfile(self, check_url_data):
        """
        Writes to data/output/check_url_out.csv.
        :return: None
        """
        # Initialize data for writing to file.
        open_mode, column_raw, outfile_name = self._write_out_file_init_data(
            check_url_data
        )
        # Write data to file.
        self._write_csv_file(outfile_name, open_mode, column_raw, check_url_data)
        self._write_outfile_final_message(check_url_data, outfile_name)

    def handle_out_file(self, check_url_data) -> None:
        """
        Check if the output file has been requested (in this case from click option "-o"),
         and writes the out report to a CSV file.\n
        :return: None
        """
        if self.outfile:
            self.write_outfile(check_url_data)

    def print_validation_result_table(self) -> None:
        """
        Prints the final Markdown-object results, the Validation Result Table.
        :return: None
        """
        print()
        self.c.print(Markdown("---\n"))
        self.c.print(Markdown(self.validation_result_table))

    def validate_url(self):
        try:
            self.process_urls()
        except InvalidInputListError as e:
            error_message = f"UNABLE to process URLs: {e}."
            self.c.print(error_message)
            sys.exit(1)
        else:
            # Append actual result tuples to self.output_report
            for self.url in self.url_list:
                self.validate()
            # Print final Validation Result Table
            self.print_validation_result_table()
            # Check if outfile has been requested and create it if necessary.
            self.handle_out_file(check_url_data=False)
            return self.validation_output_report

    # ################################### START OF CHECK PROCESS ################################### #

    def create_validation_result_lists(self) -> None:
        """
        Filters out all valid URLs from the Validation Output Report
        with the results from the validation process ("validate_url()" function).
        :return: None
        """
        for record in self.validation_output_report:
            if "True" in record[2]:
                self.valid_url_records.append(record)
            else:
                self.invalid_url_records.append(record)
        if self.sending_get_request:
            self.get_request_output_report = self.valid_url_records
        else:
            self.head_request_output_report = self.valid_url_records

    def send_head_requests(self, url_record, requests_left, total_requests) -> None:
        self.url, self.url_is_valid = url_record[1:]
        try:
            self.response = requests.head(self.url.strip())
        except requests.RequestException as e:
            self.c.print(f"HEAD request failed for URL {self.url}: {e}")
        else:
            self.c.print(
                f"Sending HEAD requests to URL '{self.url.strip()}'. "
                f"Request left {requests_left} total requests {total_requests}. ",
                end="\r",
            )

    def send_get_requests(self, record, requests_left, total_requests) -> None:
        self.url, self.url_is_valid = record[1:]
        try:
            self.response = requests.get(self.url.strip())
        except requests.RequestException as e:
            self.c.print(f"GET request failed for URL {self.url.strip()}: {e}")
        else:
            self.c.print(
                f"Sending GET requests to URL '{self.url}'. "
                f"Request left {requests_left} total requests {total_requests}. ",
                end="\r",
            )

    def get_http_status_record(self) -> tuple:
        """
        It parses the Status Record for a given status code from the full data table with codes and descriptions.
        :return: Group, Status Code, Category and Description tuple.
        """
        for self.group, status_code, category, description in self.data_table:
            if str(self.response.status_code) in str(status_code):
                return self.group, status_code, category, description

    def _set_output_report(self, output_tuple):
        if self.sending_head_request:
            self.head_request_output_report = list(self.head_request_output_report)
            self.head_request_output_report.append(output_tuple)
        if self.sending_get_request:
            self.get_request_output_report = list(self.get_request_output_report)
            self.get_request_output_report.append(output_tuple)

    def update_check_result_table(self) -> None:
        """
        Parses status code record from the internal app database for the current self.url.
        It creates the URL record (message) then updates the Check Result Table which will be
        displayed at the end.\n
        Finally populates the Head Request Output Report which is the final Check Url data
        the app will return with the Check Head process.
        :return: None
        """
        # Parse response status (code) record
        self.status_record = self.get_http_status_record()
        # Update Request (Check) Result Table
        try:
            message = f"| {self.status_record[1]} | {self.url} | {self.status_record[2]} | {self.status_record[3]} | \n"
        except TypeError as e:
            error_message = f"Unable to update Check Result Table: {e}"
            log_error_and_raise_exception(
                rev_log, error_message, InvalidURLError(error_message)
            )
        else:
            if self.sending_get_request:
                self.check_result_table = self.check_result_table.replace(
                    "**HEAD Requests Results**", "**GET Requests Results**"
                )
            self.check_result_table += message
            # Populate Head Request Output Report
            output_tuple = (
                self.status_record[1],
                self.url,
                self.status_record[2],
                self.status_record[3],
            )
            # Select appropriate Output Records
            self._set_output_report(output_tuple)

    def _select_output_report(self) -> list | tuple:
        """
        Set the 'report' value to a different Output Record based on request type (HEAD, GET, Validate)
        :return: Output Report: 'validation_output_report', 'head_request_output_report',or 'get_request_output_report'.
        """
        if self.sending_head_request:
            report = self.head_request_output_report
        elif self.sending_get_request:
            report = self.get_request_output_report
        else:
            report = self.validation_output_report
        return report

    def _select_type_and_send_request(
        self, record, requests_left, total_requests
    ) -> None:
        """
        Calls the Send HEAD or Send GET request methods, based on what has been requested in the command line.
        :param record: Tuple from the Output Record containing the target URLs
        :param requests_left: Counter parameter len of report
        :param total_requests:
        :return:
        """
        if self.sending_head_request:
            self.send_head_requests(record, requests_left, total_requests)
        if self.sending_get_request:
            self.send_get_requests(record, requests_left, total_requests)

    def send_requests(self):
        # Set the 'report' value to a different Output Record based on request type (HEAD, GET, Validate)
        report = self._select_output_report()
        total_requests = len(report)
        requests_left = total_requests
        # Send a request for each URL
        for record in report:
            self._select_type_and_send_request(record, requests_left, total_requests)
            requests_left -= 1
            # Get HTTP status URL record and update self.check_result_table
            try:
                self.update_check_result_table()
            except InvalidURLError as e:
                error_message = f"Error sending the request: {e}."
                self.c.print("\n", error_message)
                sys.exit(1)

    def print_check_result_table(self) -> None:
        """
        Prints the Check Result Table. This is the final table the app
        displays at the end with the results from the HEAD requests.
        :return: None
        """
        self.c.print(Markdown("---\n"))
        print()
        self.c.print(Markdown(self.check_result_table))

    def send_head_request(self):
        self.sending_head_request = True
        # Validate URLs:
        try:
            self.validate_url()
        except InvalidURLError as e:
            error_message = f"URL validation FAILED: {e}."
            log_error_and_raise_exception(
                rev_log, error_message, TypeError(error_message)
            )
        else:
            # Create valid and invalid URL lists
            self.create_validation_result_lists()
            # Send HEAD requests, collect and print responses.
            self.send_requests()
            # Print the main output, the check result table.
            self.print_check_result_table()
            # Handler which merely calls the self.write_outfile() function
            self.handle_out_file(check_url_data=True)
            self.sending_head_request = False
            # Return HEAD request responses
            return self.head_request_output_report

    # ################################### START OF SEND GET REQUESTS PROCESS ################################### #

    def send_get_request(self):
        self.sending_get_request = True
        try:
            self.validate_url()
        except InvalidURLError as e:
            error_message = f"URL validation FAILED: {e}."
            log_error_and_raise_exception(
                rev_log, error_message, TypeError(error_message)
            )
        else:
            # Create valid and invalid URL lists
            self.create_validation_result_lists()
            # Send GET requests, collect and print responses.
            self.send_requests()
            # Print the main output, the check result table.
            self.print_check_result_table()
            # Handler which merely calls the self.write_outfile() function
            self.handle_out_file(check_url_data=True)
            self.sending_get_request = False
            # Return HEAD request responses
            return self.get_request_output_report


@click.command(
    help=(
        "This app is an URL checker. It checks the validity of an URL, and checks the target host with head or get "
        "requests."
    )
)
@click.argument("urls", nargs=-1, required=False, metavar="[url_1] [url_2] [...]")
@click.option(
    "-l",
    "--url-list",
    "url_list",
    help="Pass a list of URLs to check.",
    # default=json.dumps([]),
    # default=json.dumps(urls_to_check),
    default=json.dumps(urls_to_check_tuple),
    required=False,
    type=json.loads,
)
@click.option(
    "-o",
    "--outfile",
    help=f"Write output to {OUTPUT_FILE_PATH}.",
    is_flag=True,
    required=False,
    default=False,
)
@click.option(
    "-v",
    "--validate-url",
    "validate_url",
    help="Validate only the URL format, don't send any requests.",
    is_flag=True,
    required=False,
    default=False,
)
@click.option(
    "-g",
    "--send-get",
    "send_get_requests",
    help="Turn on this flag to send GET requests in place of the lighter HEAD requests.",
    is_flag=True,
    required=False,
    default=False,
)
def main(urls, url_list, outfile, validate_url, send_get_requests):
    uc = UrlChecker(urls, url_list, outfile)
    if validate_url:
        try:
            uc.validate_url()
        except TypeError as e:
            Console().print(f"URL validation FAILED: {e}.")
            sys.exit(1)

    elif send_get_requests:
        try:
            uc.send_get_request()
        except TypeError as e:
            Console().print(f"URL check GET FAILED: {e}.")
            sys.exit(1)
    else:
        try:
            uc.send_head_request()
        except TypeError as e:
            Console().print(f"URL check HEAD FAILED: {e}.")
            sys.exit(1)


if __name__ == "__main__":
    main()
