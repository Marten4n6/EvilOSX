# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import subprocess
from os import listdir, path


def run_command(command):
    out, err = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    output = out + err

    if len(output.split("\n")) == 2:
        # Singe line response.
        return output.replace("\n", "")
    else:
        return output


def run(options):
    base_path = "/Users/%s/Library/Application Support/MobileSync/Backup/" % run_command("whoami")
    backup_paths = listdir(base_path)

    if len(backup_paths) > 0:
        string_builder = "Looking for backups...\n"

        for i, backup_path in enumerate(backup_paths):
            string_builder += "[+] Device: " + str(i + 1) + "\n"

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

            backup_path = path.join(base_path, backup_path, "Info.plist").replace(" ", "\\ ")

            for key in plist_keys:
                string_builder += "%s: %s\n" % (
                    key, run_command("/usr/libexec/PlistBuddy -c 'Print :\"%s\"' %s" % (key, backup_path))
                )

        print(string_builder)
    else:
        print("No local backups found.")
