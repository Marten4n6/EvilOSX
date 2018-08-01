# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import sqlite3
from os import path


def print_safari_history(history_limit, output_file):
    try:
        safari_history = path.expanduser("~/Library/Safari/History.db")
        string_builder = ""

        if path.isfile(safari_history):
            database = sqlite3.connect(safari_history)
            cursor = database.cursor()

            cursor.execute(
                "SELECT datetime(hv.visit_time + 978307200, 'unixepoch', 'localtime') "
                "as last_visited, hi.url, hv.title "
                "FROM history_visits hv, history_items hi WHERE hv.history_item = hi.id;"
            )
            statement = cursor.fetchall()

            number = history_limit * -1

            if not output_file:
                string_builder += "Safari history: \n"

                for item in statement[number:]:
                    string_builder += " -> ".join(item)
                    string_builder += "\n"
            else:
                with open(output_file, "a+") as out:
                    for item in statement[number:]:
                        out.write(str(item) + "\n")
                    out.write("\n")

            database.close()
            print(string_builder)
    except Exception as ex:
        print("[safari] Error: " + str(ex))


def print_chrome_history(history_limit, output_file):
    try:
        chrome_history = path.expanduser("~/Library/Application Support/Google/Chrome/Default/History")
        string_builder = ""

        if path.isfile(chrome_history):
            database = sqlite3.connect(chrome_history)
            cursor = database.cursor()

            cursor.execute(
                "SELECT datetime(last_visit_time/1000000-11644473600, unixepoch) "
                "as last_visited, url, title, visit_count "
                "FROM urls;"
            )
            statement = cursor.fetchall()

            number = history_limit * -1

            if not output_file:
                string_builder += "Chrome history: "

                for item in statement[number:]:
                    string_builder += item
                    string_builder += "\n"
            else:
                # Write output to file.
                with open(output_file, "a+") as out:
                    for item in statement[number:]:
                        out.write(str(item) + "\n")

            database.close()
            print(string_builder)
    except Exception as ex:
        print("[chrome] Error: " + str(ex))


def run(options):
    print_safari_history(options["history_limit"], options["output_file"])
    print_chrome_history(options["history_limit"], options["output_file"])

    if options["output_file"]:
        print("[browser_history] History saved to: " + options["output_file"])
