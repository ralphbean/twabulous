""" Twabulous

It's like twitter + fabulous.
"""

import simplejson
import pycurl
import tempfile
import fabulous.text
import fabulous.color
import urllib
import os
import re
import optparse


def parse_opts():
    """ Just parse some command line arguments """

    parser = optparse.OptionParser()
    parser.add_option(
        '-u', '--username',
        dest='username', default=None,
        help='Your twitter username')
    parser.add_option(
        '-p', '--password',
        dest='password', default=None,
        help='Your twitter password')
    parser.add_option(
        '-i', '--with-images',
        dest='images', default=False,
        action="store_true",
        help='Display twitter avatars?')

    opts, args = parser.parse_args()

    if not opts.username:
        parser.print_help()
        raise ValueError("You must supply a username")

    if not opts.password:
        parser.print_help()
        raise ValueError("You must supply a password")

    return opts


def do_image(obj):
    """ Download, fabulize, and print a user's profile avatar """

    lnk = obj['user']['profile_image_url']
    local_file = tempfile.mkstemp()[1]
    urllib.urlretrieve(lnk, local_file)

    import fabulous.image
    print fabulous.image.Image(local_file)

    os.remove(local_file)


def main():
    """ Main entry point.  This is exposed as the 'twabulous' command """

    opts = parse_opts()

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
        """ Callback passed to pyCURL.

        Each time we get a tweet, this method is called.  We jsonify the
        message, colorize and print it.

        If the user specifies --with-images, then we also download and print
        out the tweeter's fabulous avatar.
        """

        obj = simplejson.loads(data)

        try:
            if not 'user' in obj:
                return

            if opts.images:
                do_image(obj)

            tstamp = ' '.join(obj['created_at'].split(' ')[:4])
            tstamp = fabulous.color.magenta(tstamp)

            if 'text' in obj:
                try:
                    # Colorizing loop.  We look for hashtags, mentions, and
                    # urls, extract them, colorize them, and recombine the
                    # tweet for future printing.
                    for lookup in of_interest:
                        things = obj['entities'][lookup['attr']]
                        things = [thing[lookup['extract']] for thing in things]

                        for thing in things:
                            item = lookup['symb'] + thing
                            toks = unicode(obj['text']).split(item)
                            # FIXME: This is kind of ugly.
                            # FIXME: This also fails sometimes.
                            obj['text'] = \
                                    toks[0] + \
                                    lookup['color'](item) + \
                                    toks[1]

                except Exception as e:
                    # TODO -- remove these traceback prints for cleanliness
                    import traceback
                    traceback.print_exc()
                    print obj['entities']
                    print fabulous.color.cyan("color failed..."), str(e)

                # The main print statement
                print tstamp, unicode(obj['text'])

        except Exception as e:
            # TODO -- remove these traceback prints for cleanliness
            import traceback
            traceback.print_exc()
            print str(e), ':('

    # End of on_receive callback definition

    # From here on out, we actually setup the pycurl connection with twitter
    # start processing.

    # TODO: make which 'stream' we subscribe to be user-configurable.  For
    # instance, the user could watch only tweets of *their followers*, or they
    # could watch the gardenhose-sample stream, or only tweets with the
    # #juggalos hashtag.
    STREAM_URL = "https://stream.twitter.com/1/statuses/sample.json"
    USER = opts.username
    PASS = opts.password

    conn = pycurl.Curl()
    conn.setopt(pycurl.USERPWD, "%s:%s" % (USER, PASS))
    conn.setopt(pycurl.URL, STREAM_URL)

    # FIXME: sometimes it just hangs... lets find out why and fix it someday
    # conn.setopt(pycurl.SOCKET_TIMEOUT, 12)

    conn.setopt(pycurl.WRITEFUNCTION, on_receive)
    conn.perform()
