#!/bin/python3

# spec
#
# Tom Trebisky  2-13-2025
#
# A Python program to talk to the
# B and W Tech Model BTC110-S spectrometer.

import os
import serial

save_path = "spectrum"

# TODO -
# allow it to figure out the baud rate on startup.
#  it will be 9600 if the device was just booted.
#  it will be 115200 if this program has been started before.

#
# First do: dnf install python3-pyserial

#
# When powered up, it spits out a bunch of characters
# that so far make no sense, then prints a nice
# greeting at 9600 baud.

# A starting point for this program was:
#   /u1/Projects/Zynq/Git_ebaz/setup/patchit
# This simply because it was a python program
#  that used the USB serial port to communicate

# Sending 'a' is the command to tell it to communicate in ascii.
# It should respond with "ACK"
# The 'A' command is different (it sets averaging)

device = "/dev/ttyUSB0"
#TIMEOUT = 2
TIMEOUT = 5

# At one time I was having trouble getting Python to
# set up the serial port baud rate correctly, but I was
#able to run picocom to set up the port, then inherit
# the setup.  This no longer seems necessary.
#setup_cmd = "picocom --noreset -b 9600 /dev/ttyUSB0"
#setup_cmd = "picocom -qrX -b 9600 " + device
#print ( setup_cmd )

# The python pyserial "read()" method reads one byte by default.
# You can ask for more, but will need to wait for the timeout
# if that many are not available.
# There is also read_until () which reads until a certain
# sequence is found ('\n' by default).
# You could do:  read_until ( "\r\n", 32 )
# HOWEVER, asking for more than you will actually get
# means that you will wait for a timeout

# read from serial port until timeout
def monitor () :
    # loop ends on a read timeout
    while True:
        reply = ser.read()
        if len(reply) == 0 :
            print ( "Timeout" )
            break

        #reply = ser.read().decode('ascii')

        try :
            areply = reply.decode('ascii')
        except UnicodeDecodeError :
            print ( "received: ", len(reply), reply, " EX" )
            break

        print ( "received: ", len(reply), reply, areply )
        #print ( reply )
        #print ( type(reply) )

# K{int}: Set the baud rate

BAUD_115200 = 0
BAUD_38400 = 1
BAUD_19200 = 2
BAUD_9600 = 3
BAUD_4800 = 4
BAUD_2400 = 5
BAUD_1200 = 6
BAUD_600 = 7

# We get the echo, then part of the ACK
# received:  1 b'K' K
# received:  1 b'2' 2
# received:  1 b'\r'
# received:  1 b'\n'
# 
# received:  1 b'A' A
# received:  1 b'C' C
# received:  1 b'K' K
# received:  1 b'\r'
# received:  1 b'\xfb'  EX

def spec_baud ( rate ) :
    cmd = f"K{rate}\n"
    ser.write ( cmd.encode('ascii') )
    buf = ser.read_until ( "\r\n", 9 );
    # We get 9 bytes if going from 9600 to 9600
    # We get 8 bytes when actually changing
    #print ( "Baud got ", len(buf) )
    #monitor ()

    if rate == BAUD_9600 :
        ser.baudrate = 9600
    if rate == BAUD_19200 :
        ser.baudrate = 19200
    if rate == BAUD_115200 :
        ser.baudrate = 115200

# We try 115200 first and send the "a" command.
# If that fails, we must be at 9600
def spec_init () :
    global ser
    baud = 115200

    ser = serial.Serial ( device, baud, timeout=TIMEOUT )
    print ( "Using port " + ser.name)

    cmd = "a\n"
    ser.write ( cmd.encode('ascii') )
    buf = ser.read ( 8 );

    if len(buf) == 8 :
        print ( "init found device at 115200" )
        return

    print ( "init resetting port to 9600" )
    ser.baudrate = 9600

    # this will fail, but it gets things in
    # the mood to accept the baud rate change
    # We typically see a 3 byte response
    # It will timeout, but that is OK in init
    # and it only happens when the baud is wrong
    cmd = "a\n"
    ser.write ( cmd.encode('ascii') )
    buf = ser.read ( 8 );
    #print ( "cleanup got ", len(buf) )

    # OK, change baud rate
    # This gets an 8 bytes response
    spec_baud ( BAUD_115200 )

    ser.write ( cmd.encode('ascii') )
    buf = ser.read ( 8 );
    if len(buf) == 8 :
        print ( "Init OK" )
        return
    print ( "Init fails" )

# We get an 8 byte reply
# 61 0d 0a 41 43 4b 0d 0a
# First we get an echo as "a\r\n"
# Then we get an ACK as "ACK\r\n"
def spec_ascii () :
    # Read until wants byte array
    term = '\r\n'.encode('ascii')

    # We must encode to bytes
    ser.write ( "a\n".encode('ascii') )

    # read echo
    buf = ser.read_until ( term, 8 );
    if len(buf) != 3 :
        print ( "Trouble in spec_ascii() :: ", len(buf) )

    # read ACK
    buf = ser.read_until ( term, 8 );
    if len(buf) != 5 :
        print ( "Trouble in spec_ascii() :: ", len(buf) )

    #print ( "Response gives us ", len(buf), " bytes" )
    #print ( buf )
    #print ( buf.decode('ascii') )
    # monitor ()

def spec_binary () :
    ser.write ( "b\n".encode('ascii') )
    buf = ser.read ( 8 );
    if len(buf) != 8 :
        print ( "Trouble in spec_binary()" )

# for windows, do we need to add '\r\n' ?
# I don't think so, but we should experiment and see
# making sure it does the right thing.
def spec_save ( path, lines ) :
    with open ( path, 'w' ) as file :
        for line in lines :
            file.write ( line + "\n" )

def spec_bsave ( path, vals ) :
    with open ( path, 'w' ) as file :
        for val in vals :
            file.write ( f"{val:05d}\n" )

# An ascii spectrum file is 14336 bytes
# This is 2048 * 7 (5 digits + "\r\n"
# Must be upper case S
# Takes about 2 seconds at 115200 baud
def spec_scan () :
    spec_ascii ()
    ser.write ( "S\n".encode('ascii') )
    # discard the echo
    buf = ser.read ( 3 )
    # discard the ACK
    buf = ser.read ( 5 )

    # this avoids a timeout (the until zero byte)
    raw_image = ser.read_until ( b'\x00', 16000 )
    #raw_image = ser.read ( 16000 )
    # print ( raw_image )
    # print ( len(raw_image) )
    if len(raw_image) != 14337 :
        print ( "spec_scan fishy 1 : ", len(raw_image) )


    # dump the null byte at the end
    # and the last \r\n
    image = raw_image[:-3].decode ( 'ascii' )
    im = image.split ( "\r\n" )
    # print ( len(im) )
    if len(im) != 2048 :
        print ( "spec_scan fishy 2 : ", len(im) )
    return im

def spec_bfix ( raw ) :
    i = 0
    n = len(raw)
    out = []
    while ( True ) :
        if i >= n :
            break
        if raw[i] == 128 :
            val = (raw[i+1] << 8) + raw[i+2]
            print ( " --- >> ", val )
            i += 3
        else :
            jump = raw[i]
            if jump > 127 :
                jump = jump - 256
            val += jump
            #print ( jump, " >> ", val )
            i += 1
        out.append ( val )
    print ( " bfix done ", len(out) )
    return out

def spec_read1 () :
        raw = ser.read ()
        if len(raw) != 1 :
            print ( "bscan2/read1 trouble :: ", len(raw) )
        return raw[0]

# Improved version of bscan.
# Because the binary protocol does nothing to show us termination
# We decode the bytes on the fly to know when to stop, thus avoiding
# the penalty of a timeout.
# I time 3 seconds to call this 10 times,
#  so 0.3 seconds per scan
def spec_bscan2 () :
    spec_binary ()
    ser.write ( "S\n".encode('ascii') )
    # discard the echo
    buf = ser.read ( 3 )
    #print ( len(buf) )
    # discard the ACK
    buf = ser.read ( 5 )

    out = []
    while ( True ) :
        bb = spec_read1 ()
        if bb == 128 :
            b1 = spec_read1 ()
            b2 = spec_read1 ()
            val = (b1 << 8) + b2
            #print ( " --- >> ", val )
        else :
            if bb > 127 :
                bb = bb - 256
            val += bb
            #print ( bb, " >> ", val )
        out.append ( val )
        if len(out) > 2048 :
            break

    # XXX - here we delete the first item to get 2048
    # but maybe we should delete the last??
    return out[1:]

# "scan" the spectrum, but read out in binary
# Must be upper case S
# I typically see 2091 bytes or so in the raw image.
#  (compage to 14336 for the ascii scan)
# Sadly, there is no null byte at the end, so I just have
#  to wait for a read timeout to know things are finished.
# We get 2049 values -- I have no idea what to make of that.

# In binary mode, each pixel is compared to the previous value.
# If the value is +/- 127, a single signed 8-bit int encodes the difference.
# If the difference is greater, a three-byte sequence is sent:
#  0x80 (flag value that the next byte is the full value),
#  {high order bits of the 16-bit uint}, {low order bits of the 16-bit uint}.
#
# Some sample data:
# b'\x80\x051\x13\x01\xf6\xfe\xe8-\xf3\xd5\xdd( \xef\xe5"\x0b\xbf\r,\xef\xdd\xff=\xf9\xf1\xdc\x15\x07\x0e\xe3\n\xf16\x12\x03\xdf\xc7\xee\xdb/'
# 01816
# 01783
# 01773
# 01751

def spec_bscan () :
    spec_binary ()
    ser.write ( "S\n".encode('ascii') )
    # discard the echo
    buf = ser.read ( 3 )
    #print ( len(buf) )
    # discard the ACK
    buf = ser.read ( 5 )

    #raw_image = ser.read_until ( "\0", 16000 )
    raw_image = ser.read ( 16000 )
    print ( raw_image )
    print ( "Bytes in raw image: ", len(raw_image) )
    return spec_bfix ( raw_image )

# ===============================================================================
# ===============================================================================

spec_init ()

print ( "Probe with ascii command" )
spec_ascii ()

#print ( "Scan ascii spectrum" )
#im = spec_scan ()
#spec_save ( save_path, im )

#print ( "Set baud to 115200" )
#spec_baud ( BAUD_115200 )
#print ( "Done setting baud" )

print ( "Scan binary spectrum" )

vals = spec_bscan2 ()
vals = spec_bscan2 ()
vals = spec_bscan2 ()
vals = spec_bscan2 ()
vals = spec_bscan2 ()
vals = spec_bscan2 ()
vals = spec_bscan2 ()
vals = spec_bscan2 ()
vals = spec_bscan2 ()
vals = spec_bscan2 ()

print ( "Zoot: ", len(vals) )
spec_bsave ( save_path, vals )

ser.close()

print ( "Done" )

# THE END
