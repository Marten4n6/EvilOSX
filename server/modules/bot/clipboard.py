# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from AppKit import NSPasteboard, NSStringPboardType
from time import time, sleep
from datetime import datetime


def run(options):
    elapsed_time = 0
    monitor_time = int(options["monitor_time"])
    output_file = options["output_file"]

    previous = ""

    while elapsed_time <= monitor_time:
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard_string = pasteboard.stringForType_(NSStringPboardType)

            if pasteboard_string != previous:
                if output_file:
                    with open(output_file, "a+") as out:
                        out.write(pasteboard_string + "\n")
                else:
                    st = datetime.fromtimestamp(time()).strftime("%H:%M:%S")
                    print("[clipboard] " + st + " - '%s'" % str(pasteboard_string).encode("utf-8"))

            previous = pasteboard_string

            sleep(1)
            elapsed_time += 1
        except Exception as ex:
            print(str(ex))

    if output_file:
        print("Clipboard written to: " + output_file)
