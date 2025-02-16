#!/bin/python3

# First do: dnf install python3-pyserial

import os
import serial

# tester
#
# Tom Trebisky  2-13-2025
#
# This is my first Python program to talk to the
# B and W Tech Model BTC110-S spectrometer.
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
#baud = 9600
baud = 19200

# At one time I was having trouble getting Python to
# set up the serial port baud rate correctly, but I was
#able to run picocom to set up the port, then inherit
# the setup.  This no longer seems necessary.
#setup_cmd = "picocom --noreset -b 9600 /dev/ttyUSB0"
#setup_cmd = "picocom -qrX -b 9600 " + device
#print ( setup_cmd )

ser = serial.Serial ( device, baud, timeout=TIMEOUT )
print ( "Using port " + ser.name)

#UnicodeDecodeError:

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
    monitor ()

    if rate == BAUD_19200 :
        ser.baudrate = 19200
    if rate == BAUD_115200 :
        ser.baudrate = 115200
    #ser.setBaudrate(115200)

    monitor ()


# We get an 8 byte reply
# 61 0d 0a 41 43 4b 0d 0a
# First we get an echo as "a\r\n"
# Then we get an ACK as "ACK\r\n"
def spec_ascii () :
    cmd = "a\n"
    # We must encode to bytes
    ser.write ( cmd.encode('ascii') )

    monitor ()

spec_ascii ()
spec_baud ( BAUD_115200 )
spec_ascii ()

print ( "Done" )
ser.close()

# THE END
