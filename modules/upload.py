from modules.helpers import ModuleABC
import os


class Module(ModuleABC):
    def __init__(self):
        self.local_file = None
        self.output_directory = None
        self.output_name = None

    def get_info(self):
        return {
            "Author": ["Marten4n6"],
            "Description": "Uploads a file to the client.",
            "References": [],
            "Task": False
        }

    def setup(self, module_input, view, successful):
        self.local_file = os.path.expanduser(module_input.prompt("Local file to upload: "))
        self.output_directory = module_input.prompt("Remote output directory: ")
        self.output_name = module_input.prompt("New file name (ENTER to skip): ")

        if not self.output_name:
            self.output_name = os.path.basename(self.local_file)

        if not os.path.exists(self.local_file):
            view.output("Local file doesn't exist!", "attention")
            successful.put(False)
        else:
            successful.put(True)

    def run(self):
        return """\
        {}:{}:{}
        """.format(self.local_file, self.output_directory, self.output_name)
