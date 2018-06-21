# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import subprocess
from glob import glob

BACKUP_PATHS = glob("/Users/*/Library/Application Support/MobileSync/Backup/*/Info.plist")


def run_command(command):
    out, err = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    output = out + err

    if len(output.split("\n")) == 2:
        # Singe line response.
        return output.replace("\n", "")
    else:
        return output


def run(options):
    if len(BACKUP_PATHS) > 0:
        string_builder = "Looking for backups..."

        for i, path in enumerate(BACKUP_PATHS):
            string_builder += "Device: " + str(i + 1)

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

            for key in plist_keys:
                string_builder += key + ": " + \
                                  run_command("/usr/libexec/PlistBuddy -c 'Print : \" %s\"' %s" % (key, path))
    else:
        print "No local backups found."
