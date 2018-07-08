# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from abc import ABCMeta, abstractmethod


class ViewABC(metaclass=ABCMeta):
    """Abstract base class for views."""

    @abstractmethod
    def output(self, line: str, prefix: str = ""):
        """Adds a line to the view."""
        pass

    @abstractmethod
    def output_separator(self):
        """Adds a separator to the view."""
        pass

    @abstractmethod
    def prompt(self, prompt_text: str, lines: list = None) -> str:
        """Prompts for user input, assumes the caller isn't on the main thread.

        :param prompt_text: The prompt text shown to the user.
        :param lines: A list of tuples containing each line and prefix.
        """

    @abstractmethod
    def set_on_command(self, callback_function):
        """Registers the command listener."""
        pass

    @abstractmethod
    def set_header_text(self, text: str):
        """Sets the header text."""
        pass

    @abstractmethod
    def set_footer_text(self, text: str):
        """Sets the footer text."""
        pass

    @abstractmethod
    def clear(self):
        """Clears the output view."""
        pass

    @abstractmethod
    def start(self):
        """Initializes the view."""
        pass
