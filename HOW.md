Spectro software -- how to use it

Software for the BTC-100 spectrometer.

This presumes you have python and the various necessary packages installed on your machine.
This does not discuss installing and/or maintaining the program.
That is the topic of another document.

Notes on my Webpage may well be very helpful:

[notes on the BTC-100 spectrometer](http://cholla.mmto.org/electronics/spectro/btc100)

The first issue is figuring out what device name you system has assigned to the USB
to serial cable connected to the spectrometer.
On my linux system this is often /dev/ttyUSB1, but varies according to what
other USB device are plugged into the system.  This can vary from 0 to 2 or other.
This is the nature of hotplug devices like USB.
On windows it is often COM3, but can be almost any COM
port from 1 through 6, and perhaps beyond!

Common assumptions are built into the program, but you can provide the name of
the USB device on the command line as:

<pre>
./spec_gui /dev/ttyUSB2
python spec_gui COM5
</pre>

I always start the program from the command line.  Examples were just given above.
On my linux machine, I just use this when the built in serial device is correct:

<pre>
./spec_gui
</pre>

You will generally see these messages on the console as it starts up:

<pre>
init spectrometer
Using port /dev/ttyUSB1
Init trouble, probably at 9600 ::  1
init resetting port to 9600
Init OK
</pre>

Then a GUI should appear, and the spectrum display should be updating at about 1 Hz.
<br>
The LED on the spectrometer should also be blinking from red to yellow
at about 1 Hz.

The GUI will undoubtedly be changed and improved, but this is how things
are at this time:

At the top right, you can choose Auto versus Fixed scaling.
The best choice is generally auto.  Fixed sets the Y scale to
be 0 to 65536, and if you are only getting 3000 counts (which is
what I get with room illumination and no fiber attached) the data
will be mashed into the bottom of the graph.

Next you see the choice of Run versus Single.  The software should
start up in "Run" and will give a continuously updating display.
I you want "single shot" behavior, select "Single" and use the
"Read" button at the lower right to capture data.

You can enter a value for averaging (the default is 1).
<br>
You can also enter a value for gain (the default is 50).
<br>
These values should only be used when in "Single" mode,
at least at this time.

There is a "Recover" button, which repeats the initialization sequence
and may be useful if the display seems to jam up.  

================ Tips for running on Windows:

I hate windows, but let's set that topic aside for the moment.

To run this software, open up a command prompt window and
do this:

cd Spectro
python spec_gui

The "mode" command may be helpful to figure out the serial port to use.
On my desktop, I use COM3 and that is the default in the software for
windows.  On my friends laptop, we needed to use COM8, i.e.

python spec_gui COM8



