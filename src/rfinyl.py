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
import sys
import RPi.GPIO as GPIO
from mpd import MPDClient

sys.path.append('../../../bzr/nfcpy'); #edit to point to nfcy directory
import nfc

MOPIDY_SERVER_PORT = 6600
ID_LOWER = 10000
ID_UPPER = 99999

ERROR_CODES = {
    1 : 'Error connecting to mopidy server', 
    2 : 'Tag read error',
    3 : 'Tag read timeout',
    4 : 'Could not find playlist',
    5 : 'Playlist limit reached',
    6 : 'Error opening tag reader',
    }

def error(error_code):
    print ERROR_CODES[error_code]
    if error_code == 1:
        pass
    elif error_code == 2:
        pass
    elif error_code == 3:
        pass
    elif error_code == 4:
        pass
    elif error_code == 5:
        pass
    elif error_code == 6:
        pass
    else:
        print "Unknown error code"


def play(rfinyl_id):
    mpd_client = MPDClient()
    mpd_client.timeout = 10;
    mpd_client.idletimeout = None
    try:
        mpd_client.connect("localhost", MOPIDY_SERVER_PORT)
    except:
        error('Error connecting to mopidy server.')
    else:
        print "Connected to mopidy server."
        playlists = mpd_client.listplaylists()
        for playlist in playlists:
            spotify_playlist = playlist['playlist'].decode('utf-8')
            print spotify_playlist
            if rfinyl_id in spotify_playlist:
                print "Found!"
                print "Loading playlist..."
                mpd_client.load(rfinyl_id)
                print "Playing playlist..."
                mpd_client.play()
                print "Closing client."
                mpd_client.close()
                return

        error('Could not find playlist %s' % rfinyl_id)


def read_tag(clf):
    after5s = lambda: time.time() - started > 5
    started = time.time()

    read_result = clf.connect(rdwr={'on-connect': None}, terminate=after5s)

    print "Found tag!"
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
        error('Error connecting to mopidy server.')
    else:
        print "Connected to mopidy server."
        print "Clearing playlist (stopping audio)."
        mpd_client.clear()
        print "Closing client."
        mpd_client.close()


def write_tag(clf, write_id=None):
    playlist_filename = 'current_playlists'
    
    with open(playlist_filename) as playlist_file:
        current_playlists = playlist_file.readlines()

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
            print "Generating random ID"
            for attempt in range(ID_LOWER, ID_UPPER + 1):
                new_id = random.randint(ID_LOWER,ID_UPPER)
                print "Generated ID: ", str(new_id)
                if new_id not in current_playlists:
                    read_result.ndef.message = nfc.ndef.Message(nfc.ndef.TextRecord(language="en", text=new_id))
                    with open(playlist_filename, 'a') as playlist_file:
                        print "Writing generated ID to file"
                        playlist_file.write(str(new_id))
                    return
            error('playlist limit reached')
        else:
            print "ID = ", write_id
            print "Writing ID to tag."
            read_result.ndef.message = nfc.ndef.Message(nfc.ndef.TextRecord(language="en", text=write_id))


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='rfinyl: streaming vinyl player')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-w', '--write', help='Write the provided ID to a tag',required=False)
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
        print "Setting up GPIO..."
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(22,GPIO.IN)
        GPIO.setup(23,GPIO.IN)
        GPIO.add_event_detect(22,GPIO.FALLING, callback=lambda x: read_tag(clf), bouncetime=500)
        GPIO.add_event_detect(23,GPIO.FALLING, callback=lambda x: stop_playback(), bouncetime=500)
        print "Entering loop. Ctrl+c to exit."
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt: #TODO: use signal handler defined within main scope to close everything
            print "Closing, cleaning up GPIO."
            GPIO.cleanup()

