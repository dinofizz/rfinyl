import sys
import random
import time
from mpd import MPDClient

sys.path.append('../../../bzr/nfcpy'); #edit to point to nfcy directory
import nfc


# assume switch moved to play position
# need to start reading and wait for a tag, timeout 5s
# if we find a tag and read the 5 digit number successfully
#   Search mpd playlists for playlist containing same id
#   if found matching id
#       begin playback
#   else
#       playlist not found error
# else if tag read failure
#   tag read error
# else if timeout
#   read timeout error

# how to determine connectivity? call connect and see result?

def connected(tag):
    print tag.ndef.message.pretty() if tag.ndef else "Sorry, no NDEF"
    rfinyl_id = nfc.ndef.TextRecord(tag.ndef.message[0]).text if tag.ndef else "Sorry, no NDEF"
    return rfinyl_id.decode('utf-8')
    #print rfinyl_id
    ##id = random.randint(10000,99999)
    ##tag.ndef.message = nfc.ndef.Message(nfc.ndef.TextRecord(language="en", text=id))

    #mpd_client.connect("localhost", 6600)
    #print(mpd_client.mpd_version)
    #playlists = mpd_client.listplaylists()
    #for playlist in playlists:
    #    spotify_playlist = playlist['playlist'].decode('utf-8')
    #    print spotify_playlist
    #    #print dir(playlist)
    #    if rfinyl_id in spotify_playlist:
    #        mpd_client.load(rfinyl_id)
    #        mpd_client.play()
    #        print "MATCH"
            

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


def read(mpd_client, clf):
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

def stop(mpd_client):
    mpd_client.connect("localhost", 6600)
    mpd_client.clear()


def new_playlist(clf):
    with open(playlist_file) as f:
            return f.readlines()

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
        for attempt in range(10000, 100000):
            new_id = random.randint(10000,99999)
            if new_id not in current_playlists:
                read_result.ndef.message = nfc.ndef.Message(nfc.ndef.TextRecord(language="en", text=new_id))
                with open(playlist_file, 'a') as f:
                    f.write(new_id)
                return
        error('playlist limit reached')


def main():
    mpd_client = MPDClient()
    mpd_client.timeout = 10;
    mpd_client.idletimeout = None

    #start mopidy client?

    clf = nfc.ContactlessFrontend('tty:USB0:pn53x')

    read(mpd_client, clf)
    #stop(mpd_client)
    #new_playlist(clf)

if __name__=="__main__":
    main()

