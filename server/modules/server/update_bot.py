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
        # todo: Logic for checking if the version breaks backwards compatibility, if so error out.

        confirm = self._view.prompt("Are you sure you want to continue [y/N]: ", (
            "You are about to update the bot to the latest (local) version.", "attention"
        )).lower()

        if not confirm or confirm == "n":
            return False, None
        else:
            return True, None
