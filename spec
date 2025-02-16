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
TIMEOUT = 2

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
    buf = ser.read_until ( "\r\n", 8 );

    if len(buf) == 8 :
        print ( "init found device at 115200" )
        return

    print ( "init resetting port to 9600" )
    ser.baudrate = 9600

    # this will fail, but it gets things in
    # the mood to accept the baud rate change
    # We typically see a 3 byte response
    cmd = "a\n"
    ser.write ( cmd.encode('ascii') )
    buf = ser.read_until ( "\r\n", 8 );
    #print ( "cleanup got ", len(buf) )

    # OK, change baud rate
    # This gets an 8 bytes response
    spec_baud ( BAUD_115200 )

    ser.write ( cmd.encode('ascii') )
    buf = ser.read_until ( "\r\n", 8 );
    if len(buf) == 8 :
        print ( "Init OK" )
        return
    print ( "Init fails" )



# We get an 8 byte reply
# 61 0d 0a 41 43 4b 0d 0a
# First we get an echo as "a\r\n"
# Then we get an ACK as "ACK\r\n"
def spec_ascii () :
    cmd = "a\n"
    # We must encode to bytes
    ser.write ( cmd.encode('ascii') )

    # This is odd -- we get both the echo and ACK
    # even though each terminates with \r\n
    buf = ser.read_until ( "\r\n", 8 );
    if len(buf) != 8 :
        print ( "Trouble in spec_ascii()" )
    #print ( "Response gives us ", len(buf), " bytes" )
    #print ( buf )
    #print ( buf.decode('ascii') )
    # monitor ()

# for windows, do we need to add '\r\n' ?
def spec_save ( path, lines ) :
    with open ( path, 'w' ) as file :
        for line in lines :
            file.write ( line + "\n" )

# An ascii spectrum file is 14336 bytes
# This is 2048 * 7 (5 digits + "\r\n"
# Must be upper case S
# Takes about 3 seconds at 115200 baud
def spec_scan () :
    ser.write ( "S\n".encode('ascii') )
    # discard the echo
    buf = ser.read ( 3 )
    # discard the ACK
    buf = ser.read ( 5 )
    raw_image = ser.read_until ( "\r\n", 16000 )
    #print ( raw_image )
    print ( len(raw_image) )

    # dump the null byte at the end
    # and the last \r\n
    image = raw_image[:-3].decode ( 'ascii' )
    im = image.split ( "\r\n" )
    print ( len(im) )
    spec_save ( save_path, im )

spec_init ()

# print ( "Probe with ascii command" )
# spec_ascii ()
#print ( "Set baud to 115200" )
spec_baud ( BAUD_115200 )
#print ( "Done setting baud" )

print ( "Set ascii" )
spec_ascii ()

print ( "Scan" )
spec_scan ()

print ( "Done" )
ser.close()

# THE END
