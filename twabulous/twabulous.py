#!/usr/bin/env python

import simplejson
import pycurl
import tempfile
#import fabulous.image
import fabulous.text
import fabulous.color
import urllib
import os
import re

def main():
    of_interest = [
        {
            'attr': 'user_mentions',
            'symb': '@',
            'color': fabulous.color.green,
            'extract': 'screen_name',
        },
        {
            'attr': 'hashtags',
            'symb': '#',
            'color': fabulous.color.red,
            'extract': 'text',
        },
        {
            'attr': 'urls',
            'symb': '',
            'color': fabulous.color.yellow,
            'extract': 'url',
        },
    ]

    def on_receive(data):
        obj = simplejson.loads(data)

        try:
            if not 'user' in obj:
                return
            lnk = obj['user']['profile_image_url']
            tstamp = ' '.join(obj['created_at'].split(' ')[:4])
            tstamp = fabulous.color.magenta(tstamp)
            local_file = tempfile.mkstemp()[1]
            urllib.urlretrieve(lnk, local_file)
            #print fabulous.image.Image(local_file)
            os.remove(local_file)
            if 'text' in obj:
                try:
                    for lookup in of_interest:
                        things = obj['entities'][lookup['attr']]
                        things = [thing[lookup['extract']] for thing in things]

                        for thing in things:
                            item = lookup['symb'] + thing
                            toks = unicode(obj['text']).split(item)
                            obj['text'] = toks[0] + lookup['color'](item) + toks[1]

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print obj['entities']
                    print fabulous.color.cyan("color failed..."), str(e)

                print tstamp,
                print unicode(obj['text'])

        except Exception as e:
            import traceback
            traceback.print_exc()
            print str(e), ':('


    STREAM_URL = "https://stream.twitter.com/1/statuses/sample.json"
    USER = "DevAccount7"
    PASS = "blahah"

    conn = pycurl.Curl()
    conn.setopt(pycurl.USERPWD, "%s:%s" % (USER, PASS))
    conn.setopt(pycurl.URL, STREAM_URL)
#FIXME: sometimes it just hangs... lets find out why and fix it someday
#conn.setopt(pycurl.SOCKET_TIMEOUT, 12)
    conn.setopt(pycurl.WRITEFUNCTION, on_receive)
    conn.perform()
