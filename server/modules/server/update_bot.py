# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self):
        return {
            "Author:": ["Marten4n6"],
            "Description": "Update the bot to the latest (local) version.",
            "References": [],
            "Stoppable": False
        }

    def setup(self, set_options):
        self._view.display_error("This feature hasn't been implemented yet!")
        return False, None
