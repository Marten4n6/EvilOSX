import os


class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Uploads a file to the client.",
            "References": [],
            "Task": False
        }
        self.local_file = None
        self.output_directory = None
        self.output_name = None

    def setup(self, module_view, output_view, successful):
        self.local_file = os.path.expanduser(module_view.prompt("Local file to upload: "))
        self.output_directory = module_view.prompt("Remote output directory: ")
        self.output_name = module_view.prompt("New file name (ENTER to skip): ")

        if not self.output_name:
            self.output_name = os.path.basename(self.local_file)

        if not os.path.exists(self.local_file):
            output_view.add("Local file doesn't exist!", "attention")
            successful.put(False)
        else:
            successful.put(True)

    def run(self):
        return """\
        %s:%s:%s
        """ % (self.local_file, self.output_directory, self.output_name)
