# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self) -> dict:
        return {
            "Author:": ["Marten4n6"],
            "Description": "Update the bot to the latest (local) version.",
            "References": [],
            "Stoppable": False
        }

    def setup(self) -> Tuple[bool, Optional[dict]]:
        self._view.output("This feature hasn't been implemented yet!", "attention")
        return False, None
