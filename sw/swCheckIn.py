#!/usr/bin/python

import httplib, urllib
import sys
import gzip
import StringIO

if len(sys.argv) != 5:
    print "Usage: " + sys.argv[0] + " <First name> <Last name>" + \
            " <Confirmation number> <Num passengers>"
    exit(-1)

numPassengers = int(sys.argv[4])

params = urllib.urlencode({'forceNewSessions': 'yes',
        'confirmationNumber': sys.argv[3],
        'firstName': sys.argv[1],
        'lastName': sys.argv[2],
        'submitButton': 'Check+In'})
headers = {"Content-type": "application/x-www-form-urlencoded",
           "Accept": "text/html,application/xhtml+xml,applicatoin/xml",
           "Accept-Encoding": "gzip,deflate,sdch"}

## Attempt to connect normally, else fallback to the proxy.
try:
    conn = httplib.HTTPSConnection("www.southwest.com")
    conn.request("POST", "/flight/retrieveCheckinDoc.html", params, headers)
except:
    print "Normal connection failed, attempting proxy"
    ## If this fails, error out.
    conn = httplib.HTTPSConnection("proxy-us.intel.com", 912)
    conn.set_tunnel("www.southwest.com", 443)
    conn.request("POST", "/flight/retrieveCheckinDoc.html", params, headers)

response = conn.getresponse()
data = response.read()

if response.msg.getheaders('Location') == []:
    print "Invalid name or confirmation number. Try again."
    exit(-1)
checkin_url = response.msg.getheaders('Location')[0]

if response.msg.getheaders('Set-cookie') != []:
    headers['Cookie'] = ";".join(response.msg.getheaders('Set-cookie'))
    print "Cookie from GET retrieveCheckinDoc: " + headers['Cookie']

print checkin_url

conn.request("GET", checkin_url, '', headers)
response = conn.getresponse()
print response.status, response.reason
data = response.read()

if response.msg.getheaders('Set-cookie') != []:
    headers['Cookie'] = ";".join(response.msg.getheaders('Set-cookie'))
    print "Cookie from GET selectPrintDocument.html: " + headers['Cookie']

#POST to selectPrintDocument.html to get viewCheckinDocument URL

params = {'printDocuments': 'Check In'}
for x in range(0, numPassengers):
    params['checkinPassengers[' + str(x) + '].selected'] = 'true'

checkin_params = urllib.urlencode(params)

conn.request("POST", checkin_url + "&" + checkin_params, '', headers)
response = conn.getresponse()
print response.status, response.reason
data = response.read()

if response.msg.getheaders('Location') == []:
    print "Hm, something broke."
    exit(-1)

if response.msg.getheaders('Set-cookie') != []:
    headers['Cookie'] = ";".join(response.msg.getheaders('Set-cookie'))
    print "Cookie from POST selectPrintDocument.html: " + headers['Cookie']

viewDoc_url = response.msg.getheaders('Location')[0]

conn.request("GET", viewDoc_url, '', headers)
response = conn.getresponse()
print response.status, response.reason
data = response.read()

#Unzip the data
data = StringIO.StringIO(data)
gzipper = gzip.GzipFile(fileobj=data)
print gzipper.read()

conn.close()
exit(0)
