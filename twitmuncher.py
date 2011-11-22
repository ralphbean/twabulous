#!/usr/bin/env python

from qpid.connection import Connection
from qpid.datatypes import Message, uuid4
from qpid.util import connect
import time
import sys
import simplejson
import pycurl
import tempfile
import pprint
import fabulous.image
import urllib

import optparse
parser = optparse.OptionParser()
parser.add_option("-t", "--targets", dest="targets", default="localhost",
                  help="comma-separated list of target hostnames running qpid")
parser.add_option("-d", "--debug", dest="debug", action="store_true",
                  help="debug what messages are being sent")
options, args = parser.parse_args()

options.targets = [t.strip() for t in options.targets.split(',')]

# Create connection and session
session_dicts = []
for target in options.targets:
    print "Attempting to setup connection with", target
    try:
        socket = connect(target, 5672)
        connection = Connection(
            socket, username='guest', password='guest',
        )
        connection.start(timeout=10000)
        session = connection.session(str(uuid4()))

        # Setup routing properties
        properties = session.delivery_properties(routing_key='http_latlon')
        session_dicts.append({
            'target': target,
            'socket': socket,
            'connection': connection,
            'session': session,
            'properties': properties,
        })
        print "    Created target", target
    except Exception as e:
        print "    Failed to create target", target
        print str(e)
        import traceback
        traceback.print_exc()

if len(session_dicts) == 0:
    print "No connections.  Dieing early."
    time.sleep(5)  # 5 seconds.
    sys.exit()

hashdict = {}
top5 = {}
def on_receive(data):
    global top5
    global hashdict
    obj = simplejson.loads(data)

    if 'entities' in obj:
        if 'hashtags' in obj['entities']:
            for tag in obj['entities']['hashtags']:
                hashdict[tag['text']] = hashdict.get(tag['text'], 0) + 1

#    if hashdict:
#        tuples = [(k, v) for k, v in hashdict.iteritems()]
#        tuples.sort(lambda a, b : -1 * cmp(a[1], b[1]))
#        dtuple = dict(tuples[:5])
#
#        if dtuple != top5:
#            pprint.pprint(dtuple)
#            top5 = dtuple

    try:
        lnk = obj['user']['profile_image_url']
        local_file = tempfile.mkstemp()[1]
        urllib.urlretrieve(lnk, local_file)
        print fabulous.image.Image(local_file)
    except Exception as e:
        print str(e)

    #pprint.pprint(obj)
    if not 'geo' in obj or not obj['geo']:
        return

    lat, lon = obj['geo']['coordinates']
    msg = simplejson.dumps({
        'lat': lat,
        'lon': lon,
    })

    if options.debug:
        print "[sending]", msg

    for d in session_dicts:
        d['session'].message_transfer(
            destination='amq.topic',
            message=Message(d['properties'], msg))

STREAM_URL = "https://stream.twitter.com/1/statuses/sample.json"
USER = "DevAccount7"
PASS = "blahah"

conn = pycurl.Curl()
conn.setopt(pycurl.USERPWD, "%s:%s" % (USER, PASS))
conn.setopt(pycurl.URL, STREAM_URL)
conn.setopt(pycurl.WRITEFUNCTION, on_receive)

print "Entering mainloop"
print "Sending to", ",".join([d['target'] for d in session_dicts])

try:
    conn.perform()
except Exception as e:
    print str(e)
finally:
    # Close session
    for d in session_dicts:
        d['session'].close(timeout=10)
