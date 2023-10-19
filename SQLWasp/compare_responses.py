#!/usr/bin/env python3.12
# compare_responses.py
import difflib
from typing import Union

from bs4 import BeautifulSoup
from rich.console import Console
from rich.markdown import Markdown


class CompareResponses:
    """
    This class is for use with the CookieVulnScanner class. It takes in a list of dictionaries
    """

    def __init__(self, response_list: list[dict[str, list]], verbose: bool = False):
        self.c = Console()
        self.response_list = response_list
        self.verbose = verbose

    # def _assert_not_404(self, response_contents: list):
    #     diff = difflib.Differ()
    #     difference = diff.compare(response_contents[0].text, response_contents[1].text)
    #     self.c.print("Difference:", ''.join([i for i in difference]))
    #     return [i for i in difference]

    def get_soup_text(self, true_response, false_response):
        true_soup = BeautifulSoup(true_response.content, features="html.parser")
        true_text = true_soup.get_text()
        false_soup = BeautifulSoup(false_response.content, features="html.parser")
        false_text = false_soup.get_text()
        return true_text, false_text

    def differ(self, true_text, false_text):
        differ = difflib.Differ()
        diff = differ.compare(true_text.splitlines(), false_text.splitlines())
        responses_difference = [d[2:] for d in diff if d.startswith("-")]
        if responses_difference:
            return responses_difference
        else:
            return False

    def _assert_equal(self, cookie_response_dict: dict, cookie_name: str):
        """
        Checks if the first two items of a list are equals.
        :return: bool
        """
        true_response, false_response = cookie_response_dict[cookie_name]
        true_text, false_text = self.get_soup_text(true_response, false_response)
        responses_difference = self.differ(true_text, false_text)
        return responses_difference

    def elaborate_responses(self, cookie_name: str, statement: str, payload_tuple: tuple) -> Union[list[str], bool]:
        """
        This method compares the responses from the crafted requests sent with the
        'True' and 'False' statements injected in the cookie, and states if the
        response contents are identical. By "content", meaning the web page returned by the
         web application, following the crafted GET request. The 'response.content'.
        :return:
        """
        if self.verbose:
            self.c.print(Markdown(f"**Comparing Requests...**\n\n---\n"))
        # Iterate through the 'self.response_list' which is alist of dictionaries.
        for cookie_response_dict in self.response_list:
            if cookie_response_dict:
                responses_difference = self._assert_equal(cookie_response_dict, cookie_name)
                if responses_difference:
                    self.c.print(
                        "\n",
                        Markdown(
                            f"[+] Cookie '{cookie_name}' may be vulnerable to cookie injection. \n\n"
                            f"* Payload:\n```sql\n{statement}\n```\n"
                            f"* Payload Tuple:\n```python\n{payload_tuple}\n```\n"
                        ), "\n",
                        style="green"
                    )
                    self.c.print(
                        Markdown(
                            f"**Text Differences Found In Responses:** \n\n\t'{str(*responses_difference)}'\n---\n\n",
                        ), "\n", style="green"
                    )
                else:
                    if self.verbose:
                        self.c.print(
                            "\n",
                            f"\\[-] Cookie '{cookie_name}' does not appear to be vulnerable to cookie injection.\n",
                            style="red"
                        )
                return responses_difference
