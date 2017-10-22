#!/usr/bin/python

#
# Based on example from:
# https://yuji.wordpress.com/2011/06/22/python-imaplib-imap-example-with-gmail/
#

import sys
import re
import imaplib
import email

if (len(sys.argv) < 4):
    print "Wrong number of args to " + sys.argv[0] + "!"
    print "Usage: python " + sys.argv[0] + " <DB file> <Gmail username> <Gmail password>"
    exit(-1)

dbfilename = sys.argv[1]
username = sys.argv[2] + "@gmail.com"
password = sys.argv[3]

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login(username, password)
mail.list()
mail.select("inbox") # connect to inbox.

# Search the inbox and return email uids
#result, data = mail.uid('search', None, "ALL")
result, data = mail.uid('search', None, "(UNSEEN)")
if data[0] is '':
    exit(-1)

def get_email_body(email_message):

    maintype = email_message.get_content_maintype()
    if maintype == 'multipart':
        for part in email_message.get_payload():
            if part.get_content_maintype() == 'text':
                ### Filter out any hyperlinks the sender accidentally inserted
                return re.sub(r'\r\n<.*?>', '', part.get_payload())
    elif maintype == 'text':
        return email_message.get_payload()

# Process the unseen emails
for email_uid in data[0].split():
    _, email_data = mail.uid('fetch', email_uid, '(RFC822)')

    email_message = email.message_from_string(email_data[0][1])

    if email_message['Subject'].lower() != "southwest":
        continue

    body = get_email_body(email_message)

    print "Adding entry: " + body

    # TODO: Validate body contents

    # TODO: If contents are invalid, reply with helpful email

    # Append body to file
    with open(dbfilename, "a") as dbfile:
        dbfile.write(body)

    # Mark the email as deleted
    mail.store(email_uid, '+FLAGS', '\\Deleted')

mail.expunge()
mail.close()
mail.logout()
