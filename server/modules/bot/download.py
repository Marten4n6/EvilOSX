# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import subprocess
import uuid
from os import path


def run_command(command):
    out, err = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    output = out + err

    if len(output.split("\n")) == 2:
        return output.replace("\n", "")
    else:
        return output


def get_file_hash(file_path):
    """:return: The MD5 hash of the specified file path."""
    return run_command("md5 " + path.realpath(file_path)).split(" = ")[1]


def upload_file(file_path, buffer_size):
    """Send back the file in pieces to the server (so we support very large files)."""
    with open(file_path, "rb") as input_file:
        while True:
            try:
                piece = input_file.read(buffer_size)

                if not piece:
                    break

                print(piece)
            except SystemExit:
                # Thrown when "kill download" is run.
                print("Stopped uploading.")
                break


def run(options):
    file_path = path.expanduser(options["file_path"])
    buffer_size = options["buffer_size"]

    if not path.exists(file_path):
        print("Failed to download file, invalid path.")
    else:
        if path.isdir(file_path):
            print("Compressing directory: " + file_path)
            zip_file = path.join("/tmp", str(uuid.uuid4()).replace("-", "")[:12] + ".zip")

            run_command("zip -r " + zip_file + " " + file_path)

            # Let the server know the output file is a zip file.
            options["response_options"]["output_name"] = options["response_options"]["output_name"] + ".zip"

            print("Started|" + get_file_hash(zip_file))
            upload_file(zip_file, buffer_size)

            print("[download] Finished.")
            run_command("rm -rf " + zip_file)
        else:
            print("Started|" + get_file_hash(file_path))
            upload_file(file_path, buffer_size)

            print("[download] Finished.")
