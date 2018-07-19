# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from abc import ABCMeta, abstractmethod
from server.model import Bot


class ViewABC(metaclass=ABCMeta):
    """Abstract base class for views, used by the background server."""

    @abstractmethod
    def on_response(self, response: str):
        """Called when a bot sends a response."""
        pass

    @abstractmethod
    def on_bot_added(self, bot: Bot):
        """Called when a bot connects for the first time."""
        pass

    @abstractmethod
    def on_bot_removed(self, bot: Bot):
        """Called when a bot gets removed."""

    @abstractmethod
    def on_bot_path_change(self, bot: Bot):
        """Called when the bot's local path changes."""
        pass
