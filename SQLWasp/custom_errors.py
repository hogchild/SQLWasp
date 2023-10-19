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


class HTTP5xxResponseException(Exception):
    def __init__(self, message="5xx (Server Errors). Server may have internal issues."):
        super().__init__(message)


class HTTP4xxResponseException(Exception):
    def __init__(self, message="4xx (Client Errors). Server is running but unable to process the request."):
        super().__init__(message)


class HTTP3xxResponseException(Exception):
    def __init__(self, message="3xx (Redirection). Server is running and redirected the request."):
        super().__init__(message)


class HTTP2xxResponseException(Exception):
    def __init__(self, message="2xx (Successful). The server successfully handled the request."):
        super().__init__(message)


class HTTP1xxResponseException(Exception):
    def __init__(self, message="1xx (Informational). Server is apparently running."):
        super().__init__(message)
