#! /usr/bin/python

# Import smtplib for the actual sending function
import smtplib
import sys
import socket

socket.setdefaulttimeout(600)

# Import the email modules we'll need
from email.mime.text import MIMEText

if (len(sys.argv) < 4):
    print "Wrong number of args to " + sys.argv[0] + "!"
    print "Usage: python " + sys.argv[0] + " <filename> <Gmail username> <Gmail password> [recipient email(s)]"
    exit(-1)

fname = sys.argv[1]
username = sys.argv[2]
password = sys.argv[3]
recipients = [username + "@gmail.com"] + sys.argv[4:]

# Open a plain text file for reading.  For this example, assume that
# the text file contains only ASCII characters.
fp = open(fname, 'rb')
# Create a text/plain message
msg = MIMEText(fp.read())
fp.close()

# me == the sender's email address
# you == the recipient's email address
msg['Subject'] = 'Check-in notification'
msg['From'] = 'from'
msg['To'] = ", ".join(recipients)

# Send the message via our own SMTP server, but don't include the
# envelope header.
s = smtplib.SMTP('smtp.gmail.com:587', timeout=600)
s.starttls()
s.login(username,password)
s.sendmail(username + "@gmail.com", recipients, msg.as_string())
s.quit()
