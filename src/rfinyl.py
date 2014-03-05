#!/usr/bin/env python
import argparse
import sys
import random
import time
from mpd import MPDClient

sys.path.append('../../../bzr/nfcpy'); #edit to point to nfcy directory
import nfc
            

def error(error):
    print error


def play(mpd_client, rfinyl_id):
    mpd_client.connect("localhost", 6600)
    playlists = mpd_client.listplaylists()
    for playlist in playlists:
        spotify_playlist = playlist['playlist'].decode('utf-8')
        #print spotify_playlist
        if rfinyl_id in spotify_playlist:
            mpd_client.load(rfinyl_id)
            mpd_client.play()
            return

    error('Could not find playlist %s' % rfinyl_id)


def read_tag(mpd_client, clf):
    after5s = lambda: time.time() - started > 5
    started = time.time()

    read_result = clf.connect(rdwr={'on-connect': None}, terminate=after5s)

    try:
        rfinyl_id = nfc.ndef.TextRecord(read_result.ndef.message[0]).text.decode('utf-8') if read_result.ndef \
                else error("read error")
    except ValueError:
        error("read error")
    except AttributeError:
        error("read timeout")
    else:
        play(mpd_client, rfinyl_id)


def stop_playback(mpd_client):
    mpd_client.connect("localhost", 6600)
    mpd_client.clear()


def write_tag(clf, write_id=None):
    print write_id
    playlist_file = 'current_playlists'
    
    with open(playlist_file) as f:
        current_playlists = f.readlines()

    after5s = lambda: time.time() - started > 5
    started = time.time()

    read_result = clf.connect(rdwr={'on-connect': None}, terminate=after5s)

    try:
        rfinyl_id = nfc.ndef.TextRecord(read_result.ndef.message[0]).text.decode('utf-8') if read_result.ndef \
                else error("read error")
    except ValueError:
        error("read error")
    except AttributeError:
        error("read timeout")
    else:
        if write_id is None:
            for attempt in range(10000, 100000):
                new_id = random.randint(10000,99999)
                if new_id not in current_playlists:
                    read_result.ndef.message = nfc.ndef.Message(nfc.ndef.TextRecord(language="en", text=new_id))
                    with open(playlist_file, 'a') as f:
                        f.write(str(new_id))
                    return
            error('playlist limit reached')
        else:
            read_result.ndef.message = nfc.ndef.Message(nfc.ndef.TextRecord(language="en", text=write_id))


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='rfinyl: streaming vinyl player')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-w','--write', help='Text to write to tage',required=False)
    group.add_argument('-r', '--read', action='store_true', required=False)
    group.add_argument('-n', '--new', action='store_true', required=False)
    group.add_argument('-s', '--stop', action='store_true', required=False)
    args = parser.parse_args()

    mpd_client = MPDClient()
    mpd_client.timeout = 10;
    mpd_client.idletimeout = None
    clf = nfc.ContactlessFrontend('tty:USB0:pn53x')

    if args.read:
        read_tag(mpd_client, clf)
    elif args.new:
        write_tag(clf)
    elif args.write:
        write_tag(clf, args.write)
    elif args.stop:
        stop_playback(mpd_client)
