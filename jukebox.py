#!/usr/bin/env python


import glob
import json
import os
import select
import socket
import subprocess
import sys
import time
import traceback

DevNull = open('/dev/null','rw')
PORT = 55555

Q = []

p = None
filename = None

def play(filename):
    p = subprocess.Popen(('play', filename),
                         stdout = DevNull,
                         stdin  = DevNull,
                         stderr = DevNull)

    return p

def playGlob(filenameGlob):
    filenames = glob.glob(filenameGlob)
    if (len(filenames) == 1):
        filename = filenames[0]
        return (filename, play(filename))
    return None

class AtomicFile(object):
    def __init__(self, filename, mode = 'w'):
        self.filename = filename
        self.new = filename + ".new"
        self.w = open(self.new, mode)

    def __enter__(self, *extra):
        #print(extra)
        return self.w

    def __exit__(self, *extra):
        #print(extra)
        self.w.close()
        os.rename(self.new, self.filename)

def process(data, address):
    global p
    global Q


    if not data: return

    print(data, address)

    if (data == 'Stop'):
        if p:
            p.kill()
        return
    if (data == 'Flush'):
        Q = []
        return
    if (data == 'Shutdown'):
        return
    if (data == 'Play'):
        return
    try:
        (letter, number) = data.split()
        Q.append((letter, number, time.time(), address))
    except:
        traceback.print_exc()

# Create a UDP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
sock.bind(('0.0.0.0', PORT))

while True:
    (r,w,x) = select.select((sock,),(),(),1)

    if r:
        (data, address) = sock.recvfrom(4096)
        process(data, address)

    if p:
        if p.poll() is not None:
            print(p.wait())
            p = None
            filename = None
        else:
            print(filename)
    if Q:
        if p:
            print(Q)
        else:
            (letter, number, epoch, address) = Q.pop(0)
            p = playGlob("/var/jukebox/%s/%s/*" % (letter, number))
            if p:
                (filename, p) = p
    elif p:
        print(filename)
    else:
        print('.')

    with AtomicFile('/dev/shm/jukebox.json') as w:
        w.write(json.dumps({'current': filename,
                            'length' : len(Q),
                            'queue'  : Q,
                            },
                           indent=4, sort_keys=1))
