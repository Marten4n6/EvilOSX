# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import platform
import subprocess
from os import getuid


def run_command(command):
    out, err = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    output = out + err

    if len(output.split("\n")) == 2:
        # Single line response.
        return output.replace("\n", "")
    else:
        return output


def get_model():
    model_key = run_command("sysctl -n hw.model")

    if not model_key:
        model_key = "Macintosh"

    output = run_command(
        "/usr/libexec/PlistBuddy -c 'Print :\"%s\"' "
        "/System/Library/PrivateFrameworks/ServerInformation.framework/Versions/A/Resources/English.lproj/SIMachineAttributes.plist "
        "| grep marketingModel" % model_key
    )

    if "does not exist" in output.lower():
        return model_key + " (running in virtual machine?)"
    else:
        return output.split("=")[1][1:]


def get_wifi():
    command = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | grep -w SSID"
    return run_command(command).replace("SSID: ", "").strip()


def get_battery():
    return run_command("pmset -g batt | egrep \"([0-9]+\\%).*\" -o | cut -f1 -d\';\'")


def run(options):
    string_builder = ""

    string_builder += "System version: %s\n" % str(platform.mac_ver()[0])
    string_builder += "Model: %s\n" % get_model()
    string_builder += "Battery: %s\n" % get_battery()
    string_builder += "WiFi network: %s\n" % get_wifi()

    if getuid() == 0:
        string_builder += "We are root!\n"
    else:
        string_builder += "We are not root :(\n"
    if "On" in run_command("fdesetup status"):
        string_builder += "FileVault is on.\n"
    else:
        string_builder += "FileVault is off."

    print(string_builder)
