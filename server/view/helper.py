# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from abc import ABCMeta, abstractmethod
from server.model import Bot


class ViewABC:
    """Abstract base class for views, used by the background server."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def output(self, line, prefix=""):
        """Adds a line to the output view.

        :type line: str
        :type prefix: str
        """
        pass

    def output_separator(self):
        self.output("-" * 5)

    @abstractmethod
    def on_response(self, response):
        """Called when a bot sends a response.

        :type response: str
        """
        pass

    @abstractmethod
    def on_bot_added(self, bot):
        """Called when a bot connects for the first time.

        :type bot: Bot
        """
        pass

    @abstractmethod
    def on_bot_removed(self, bot):
        """Called when a bot gets removed.

        :type bot: Bot
        """

    @abstractmethod
    def on_bot_path_change(self, bot):
        """Called when the bot's local path changes.

        :type bot: Bot
        """
        pass
