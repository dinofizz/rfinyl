#!/usr/bin/env python
##
# @file rfinyl.py
# @brief Streaming vinyl player
# @author Dino Fizzotti
# @version v1
# @date 2014-03-05
import argparse
import sys
import random
import time
import RPi.GPIO as GPIO
from mpd import MPDClient

sys.path.append('../../../bzr/nfcpy'); #edit to point to nfcy directory
import nfc

MOPIDY_SERVER_PORT = 6600
ID_LOWER = 10000
ID_UPPER = 99999

def testbtn (bleh):
    print bleh

def play_button (pin):
    print "handling play button event"
    print pin 


def record_button (pin):
    print "handling record button event"


def error(error):
    print error


def play(rfinyl_id):
    mpd_client = MPDClient()
    mpd_client.timeout = 10;
    mpd_client.idletimeout = None
    try:
        mpd_client.connect("localhost", MOPIDY_SERVER_PORT)
    except:
        error('Error connecting to mopidy server')
    else:
        playlists = mpd_client.listplaylists()
        for playlist in playlists:
            spotify_playlist = playlist['playlist'].decode('utf-8')
            print spotify_playlist
            if rfinyl_id in spotify_playlist:
                mpd_client.load(rfinyl_id)
                mpd_client.play()
                mpd_client.close()
                return

        error('Could not find playlist %s' % rfinyl_id)


def read_tag(clf):
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
        print "Found tag", rfinyl_id
        play(rfinyl_id)


def stop_playback():
    # Tried to create this object in main and pass it around with the button callbacks
    # but had connection problems ("broken pipe"), so this is why I am creating and
    # closing on each call
    mpd_client = MPDClient()
    mpd_client.timeout = 10;
    mpd_client.idletimeout = None
    
    try:
        mpd_client.connect("localhost", MOPIDY_SERVER_PORT)
    except:
        error('Error connecting to mopidy server')
    else:
        mpd_client.clear()
        mpd_client.close()


def write_tag(clf, write_id=None):
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
            for attempt in range(ID_LOWER, ID_UPPER + 1):
                new_id = random.randint(ID_LOWER,ID_UPPER)
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
    group.add_argument('-w','--write', help='Write the provided ID to a tag',required=False)
    group.add_argument('-r', '--read', help='Read a tag', action='store_true', required=False)
    group.add_argument('-n', '--new', help='Write a new random ID to a tag', action='store_true', required=False)
    group.add_argument('-s', '--stop', help='Stop mopidy playback', action='store_true', required=False)
    group.add_argument('-d', '--daemon', help='Run rfinyl as daemon', action='store_true', required=False)
    args = parser.parse_args()
    
    try:
        clf = nfc.ContactlessFrontend('tty:USB0:pn53x')
    except IOError:
        error('RFID open device error')
        exit(1)

    if args.read:
        read_tag(clf)
    elif args.new:
        write_tag(clf)
    elif args.write:
        write_tag(clf, args.write)
    elif args.stop:
        stop_playback()
    elif args.daemon:
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(22,GPIO.IN)
        GPIO.setup(23,GPIO.IN)

        GPIO.add_event_detect(22,GPIO.FALLING, callback=lambda x: read_tag(clf), bouncetime=500)
        GPIO.add_event_detect(23,GPIO.FALLING, callback=lambda x: stop_playback(), bouncetime=500)

        while True:
            time.sleep(1)

        GPIO.cleanup()
