#!/usr/bin/env python3.12
# reverse_logger.py ver 1.0
import os
import logging
import traceback

import rich.errors
from rich.console import Console
from logging.handlers import RotatingFileHandler

from rich.markdown import Markdown

# from reverse_server_error_classes import PermissionDeniedError

c = Console()


class PermissionDeniedError(Exception):
    """Exception raised for JSON encoding errors."""

    def __init__(self, message="Permission denied writing to disk."):
        super().__init__(message)


def log_error_and_raise_exception(logger_obj: "ReverseLogger", error_message: str | Markdown, exception: Exception):
    logger_obj.log_exception(error_message)
    raise exception from None


def log_error(logger_obj, error_message: str | Markdown) -> None:
    logger_obj.log_exception(error_message)
    c.print(error_message)


def log_info(
        logger_obj,
        info_message: str | Markdown,
        lineno: int,
        style: str = None,
        debug_mode=True,  # True or False. line to print only lineno and not filename
        stdout_debug=True,
        print_anyway=False,
) -> None:
    record = logging.LogRecord(
        name=logger_obj.logger.name,
        level=logging.INFO,
        pathname=logger_obj.logger.name + ".py",
        lineno=lineno,
        msg=info_message,
        args=(),
        exc_info=None,
        func=None,
        sinfo=None,
    )
    logger_obj.logger.handle(record)
    try:
        if stdout_debug:
            if debug_mode == "line":
                if style:
                    c.print(f"[Line: {lineno}]: ", info_message, style=style)
                else:
                    c.print(f"[Line: {lineno}]: ", info_message)
            elif debug_mode:
                if style:
                    c.print(f"[Line: {lineno}]: \\[{record.pathname}]: ", info_message, style=style)
                else:
                    c.print(f"[Line: {lineno}]: \\[{record.pathname}]: ", info_message)
            elif not debug_mode:
                if style:
                    c.print(info_message, style=style)
                else:
                    c.print(info_message)
        elif not stdout_debug:
            if print_anyway:
                if style:
                    c.print(info_message, style=style)
                else:
                    c.print(info_message)
    except (rich.errors.MarkupError, Exception) as e:
        error_message = (
            f"[i] Unable to pretty print command output: {e}.\n"
            f"\tFalling back to built-in print function.\n"
        )
        print(error_message)
        print(info_message)


def filename_parser(
        log_folder_name: str = "rev_logger_logs",
        log_file_name: str = __file__,
) -> tuple[str, str]:
    """
    Retrieve the file name of the script, remove the file extension,
    and return a tuple containing the file name without extension
    and the corresponding log file path.

    :param log_folder_name: The name of the log folder (default: 'rev_logger_logs').
    :param log_file_name: The file name of the script (default: __file__).

    :return: A tuple containing the file name without extension (str) and the log file path (str).

    :raises PermissionDeniedError: If there is an error while creating the log folder or file due to file corruption
        or permission denial.

    :raises TypeError: If the provided log_folder_name or log_file_name is not a string.

    :raises ValueError: If the provided log_folder_name or log_file_name is an empty string.

    :raises OSError: If there are any other issues while creating the log folder or file.
    """
    if not isinstance(log_folder_name, str):
        raise TypeError("log_folder_name must be a string.")

    if not isinstance(log_file_name, str):
        raise TypeError("log_file_name must be a string.")

    if not log_folder_name:
        raise ValueError("log_folder_name cannot be an empty string.")

    if not log_file_name:
        raise ValueError("log_file_name cannot be an empty string.")

    file_name = os.path.basename(log_file_name)
    file_name_no_ext = os.path.splitext(file_name)[0]
    log_folder_path = os.path.join(os.getcwd(), log_folder_name)

    try:
        if not os.path.exists(log_folder_path):
            os.mkdir(log_folder_path)
        log_file_path = os.path.join(log_folder_path, file_name_no_ext + ".log" or "log")
        return file_name_no_ext, log_file_path
    except OSError as e:
        error_message = f"Error while creating the log folder or file: {e}."
        c.log(error_message)
        raise PermissionDeniedError(error_message)


filename, log_filepath = filename_parser(log_file_name=__file__)


class ReverseLogger:
    def __init__(
            self,
            logger_name=filename,
            log_file_path=log_filepath,
            encoding="utf8",
            logging_level=logging.DEBUG,

    ):
        self.logger_name = logger_name
        self.logging_level = logging_level
        self.log_file_path = log_file_path
        self.logger = None
        self.max_file_size_bytes = None
        self.backup_count = 0
        self.file_handler = None
        self.encoding = encoding
        self.formatter = None
        self.create_logger()

    # Create a logger
    def create_logger(self):
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(self.logging_level)
        self.create_rotating_file_handler()

    # Create Exception custom logger
    def log_exception(self, message):
        self.logger.error(message)
        self.logger.exception("Exception occurred:\n%s", traceback.format_exc())

    # Create a rotating file handler
    def create_rotating_file_handler(self):
        self.max_file_size_bytes = 100 * 1024 * 1024  # 100 MB
        self.backup_count = 1  # Number of backup log files to keep
        self.file_handler = RotatingFileHandler(
            self.log_file_path,
            maxBytes=self.max_file_size_bytes,
            backupCount=self.backup_count,
            encoding=self.encoding,
        )
        self.file_handler.setLevel(self.logging_level)
        self.create_formatter()

    # Create a formatter and add it to the file handler
    def create_formatter(self):
        self.formatter = logging.Formatter('%(asctime)s: %(name)s: [Line: %(lineno)d]: %(levelname)s: %(message)s')
        self.file_handler.setFormatter(self.formatter)
        self.add_handler_to_logger()

    # Add the file handler to the logger
    def add_handler_to_logger(self):
        self.logger.addHandler(self.file_handler)


# Log messages
def main():
    rev_logger = ReverseLogger(logging_level=logging.DEBUG)
    rev_logger.logger.debug('This is a debug message')
    rev_logger.logger.info('This is an informational message')
    rev_logger.logger.warning('This is a warning message')
    rev_logger.logger.error('This is an error message')


if __name__ == "__main__":
    main()
