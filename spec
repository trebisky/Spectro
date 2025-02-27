#!/bin/python3

# spec
#
# Tom Trebisky  2-13-2025
#
# A Python program to talk to the
# B and W Tech Model BTC100-S spectrometer.

import os
import sys
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

# Baudrate codes for the BTC100 "K" command
BAUD_115200 = 0
BAUD_38400 = 1
BAUD_19200 = 2
BAUD_9600 = 3
BAUD_4800 = 4
BAUD_2400 = 5
BAUD_1200 = 6
BAUD_600 = 7

# At one time I was having trouble getting Python to
# set up the serial port baud rate correctly, but I was
# able to run picocom to set up the port, then inherit
# the setup.  This no longer seems necessary.
#  setup_cmd = "picocom --noreset -b 9600 /dev/ttyUSB0"
#  setup_cmd = "picocom -qrX -b 9600 " + device
#  print ( setup_cmd )

# The python pyserial "read()" method reads one byte by default.
# You can ask for more, but will need to wait for the timeout
# if that many are not available.
# There is also read_until () which reads until a certain
# sequence is found ('\n' by default).
# You could do:  read_until ( "\r\n", 32 )
# HOWEVER, asking for more than you will actually get
# means that you will wait for a timeout

class Spectro () :
    def __init__ ( self, device ) :
        baud = 115200
        TIMEOUT = 2

        try:
            ser = serial.Serial ( device, baud, timeout=TIMEOUT )
        except serial.SerialException as e:
            print ( f"Cannot open serial port {device}: {e}")
            exit ()
        except FileNotFoundError as e:
            print ( f"Cannot open serial port {device}: {e}")
            exit ()

        print ( "Using port " + ser.name)

        ser.write ( "a\n".encode('ascii') )
        buf = ser.read ( 8 )

        if len(buf) == 8 :
            print ( "init found device at 115200" )
            print ( "Init OK" )
            self.ser = ser
            return

        print ( "Init trouble, probably at 9600 :: ", len(buf) )

        print ( "init resetting port to 9600" )
        ser.baudrate = 9600

        # this will fail, but it gets things in
        # the mood to accept the baud rate change
        # We typically see a 3 byte response
        # It will timeout, but that is OK in init
        # and it only happens when the baud is wrong
        ser.write ( "a\n".encode('ascii') )
        buf = ser.read ( 8 )
        #print ( "cleanup got ", len(buf) )

        # OK, change baud rate
        # This gets an 8 bytes response
        #spec_baud ( BAUD_115200 )
        rate = BAUD_115200
        cmd = f"K{rate}\n"
        ser.write ( cmd.encode('ascii') )
        buf = ser.read_until ( "\r\n", 9 )
        ser.baudrate = 115200

        # check again with the "a" command
        ser.write ( "a\n".encode('ascii') )
        buf = ser.read ( 8 )
        if len(buf) == 8 :
            print ( "Init OK" )
            self.ser = ser
            return

        self.ser = None
        print ( "Init fails" )

    def finish ( self ) :
        self.ser.close()
        print ( "Done" )

    # Tell the BTC100 to change baud rate
    # (this is a bit of a cat and mouse game as we
    #  must also change our baud rate to match)
    #
    # K{int}: Set the baud rate
    # We always get the echo
    # We get only part of the ACK when the rate changes
    # (the last byte gets mangled)

    def baud ( self, rate ) :
        ser = self.ser

        cmd = f"K{rate}\n"
        ser.write ( cmd.encode('ascii') )
        buf = ser.read_until ( "\r\n", 9 )
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

    # useful during debug, no longer used.
    # read from serial port until timeout
    def monitor ( self ) :
        # loop ends on a read timeout
        while True:
            reply = ser.read()
            if len(reply) == 0 :
                print ( "Timeout" )
                break

            try :
                areply = reply.decode('ascii')
            except UnicodeDecodeError :
                print ( "received: ", len(reply), reply, " EX" )
                break

            print ( "received: ", len(reply), reply, areply )

    # Set how many spectra to average
    def average ( self, val ) :
        cmd = f"A{val}\n"
        expect = len(cmd) + 1 + 5
        self.ser.write ( cmd.encode('ascii') )
        buf = self.ser.read_until ( "\r\n", expect )

    # Set integration time in ms (50-65000)
    def integ ( self, val ) :
        cmd = f"I{val}\n"
        expect = len(cmd) + 1 + 5
        self.ser.write ( cmd.encode('ascii') )
        buf = self.ser.read_until ( "\r\n", expect )

    # reset the spectrometer (never used)
    def reset ( self ) :
        cmd = "Q\n"
        self.ser.write ( cmd.encode('ascii') )
        buf = self.ser.read_until ( "\r\n", 8 )

    # We get an 8 byte reply
    # 61 0d 0a 41 43 4b 0d 0a
    # First we get an echo as "a\r\n"
    # Then we get an ACK as "ACK\r\n"
    def ascii ( self ) :
        # Read until wants byte array
        term = '\r\n'.encode('ascii')
        ser = self.ser

        # We must encode to bytes
        ser.write ( "a\n".encode('ascii') )

        # read echo
        buf = ser.read_until ( term, 8 )
        if len(buf) != 3 :
            print ( "Trouble in spec_ascii() :: ", len(buf) )

        # read ACK
        buf = ser.read_until ( term, 8 )
        if len(buf) != 5 :
            print ( "Trouble in spec_ascii() :: ", len(buf) )

        #print ( "Response gives us ", len(buf), " bytes" )
        #print ( buf )
        #print ( buf.decode('ascii') )
        # monitor ()

    def binary ( self ) :
        ser = self.ser

        ser.write ( "b\n".encode('ascii') )
        buf = ser.read ( 8 )
        if len(buf) != 8 :
            print ( "Trouble in spec_binary()" )

    # for windows, do we need to add '\r\n' ?
    # I don't think so, but we should experiment and see
    # making sure it does the right thing.
    def asave ( self, path, lines ) :
        with open ( path, 'w' ) as file :
            for line in lines :
                file.write ( line + "\n" )

    def bsave ( self, path, vals ) :
        with open ( path, 'w' ) as file :
            for val in vals :
                file.write ( f"{val:05d}\n" )

    def read1 ( self ) :
        raw = self.ser.read ()
        if len(raw) != 1 :
            print ( "bscan2/read1 trouble :: ", len(raw) )
        return raw[0]

    # "scan" the spectrum, but read out in binary
    # Must be upper case S
    # I typically see 2091 bytes or so in the raw image.
    #  (compage to 14336 for the ascii scan)
    # There is no null byte at the end.
    # We get 2049 values -- I have no idea what to make of that.

    # In binary mode, each pixel is compared to the previous value.
    # If the value is +/- 127, a single signed 8-bit int encodes the difference.
    # If the difference is greater, a three-byte sequence is sent:
    #  0x80 (flag value that the next byte is the full value),
    #  {high order bits of the 16-bit uint}, {low order bits of the 16-bit uint}.

    # Improved version of bscan.
    # Because the binary protocol does nothing to show us termination
    # We decode the bytes on the fly to know when to stop, thus avoiding
    # the penalty of a timeout.
    # I time 3 seconds to call this 10 times,
    #  so 0.3 seconds per scan
    def bscan ( self ) :
        ser = self.ser

        self.binary ()
        ser.write ( "S\n".encode('ascii') )
        # discard the echo
        buf = ser.read ( 3 )
        #print ( len(buf) )
        # discard the ACK
        buf = ser.read ( 5 )

        out = []
        while ( True ) :
            bb = self.read1 ()
            if bb == 128 :
                b1 = self.read1 ()
                b2 = self.read1 ()
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

    # Read out via ascii.
    # -- there is little reason to use this with bscan available.
    #
    # An ascii spectrum file is 14336 bytes
    # This is 2048 * 7 (5 digits + "\r\n"
    # Must be upper case S
    # Takes about 2 seconds at 115200 baud
    def ascan ( self ) :
        self.ascii ()
        ser = self.ser

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

# ===============================================================================
# ===============================================================================

# on Windows 10, os.name returns "nt".
#   on Linux it returns "posix"
# on Windows 10, sys.platform returns "win32".
#   on Linux it returns "linux"
#print ( os.name )
#print ( sys.platform )

if ( sys.platform == "linux" ) :
    spec_device = "/dev/ttyUSB0"
else :
    spec_device = "COM3"

s = Spectro ( spec_device )

#spec_init ()

print ( "Probe with ascii command" )
s.ascii ()

#print ( "Scan ascii spectrum" )
#im = spec_scan ()
#spec_save ( save_path, im )

#print ( "Set baud to 115200" )
#spec_baud ( BAUD_115200 )
#print ( "Done setting baud" )

print ( "Scan binary spectrum" )

s.average ( 10 )
vals = s.bscan ()

#vals = spec_bscan2 ()
#vals = spec_bscan2 ()
#vals = spec_bscan2 ()
#vals = spec_bscan2 ()
#vals = spec_bscan2 ()
#vals = spec_bscan2 ()
#vals = spec_bscan2 ()
#vals = spec_bscan2 ()
#vals = spec_bscan2 ()
#vals = spec_bscan2 ()
#print ( "Zoot: ", len(vals) )

s.bsave ( save_path, vals )

s.finish ()

# THE END
