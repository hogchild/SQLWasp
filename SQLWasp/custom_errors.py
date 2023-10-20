#!/usr/bin/env python3.12
# custom_errors.py


class CookieInjectorGetResponseError(Exception):
    def __init__(self, message="Error communicating with server."):
        super().__init__(message)


class InvalidURLError(Exception):
    def __init__(self, message="Detected invalid URL."):
        super().__init__(message)


class InvalidInputListError(Exception):
    def __init__(self, message="Invalid list-syntax detected in input."):
        super().__init__(message)


class CheckLatencyConsistencyError(Exception):
    def __init__(self, message="Error checking latency consistency."):
        super().__init__(message)


class AssessURLRequestError(Exception):
    def __init__(self, message="Request error assessing URL."):
        super().__init__(message)