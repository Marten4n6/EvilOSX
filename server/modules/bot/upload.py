# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from os import path
import urllib2


def run(options):
    download_url = "http://%s:%s/%s" % (options["server_host"], options["server_port"], options["download_path"])
    output_path = path.join(options["output_dir"], options["output_name"])

    with open(output_path, "wb") as output_file:
        output_file.write(urllib2.urlopen(download_url).read())
        output_file.close()  # Important!

    print("File downloaded finished, saved to: " + output_path)
