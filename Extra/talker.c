/* I began this 2-13-2025 to get started,
 * but then moved to "spec" which is written in Python.
 * Tom Trebisky  2-14-2025
 */
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <stdlib.h>

char *device = "/dev/ttyUSB0";
char *outfile = "spectrum";

#define BSIZE	64
#define BSIZE2	16*1024

char image[BSIZE2];

/* using "man termios" gives information about this mess.
 * note that the baud rate constants in no way correspond
 * to the baud rated numbers.
 * For example B9600 is 13.
 */
int
setup ( char *device )
{
		int fd;
		int x;
		struct termios tt;
		int speed;

		fd = open ( device, O_RDWR );
		printf ( "fd = %d\n", fd );

		x = tcgetattr ( fd, &tt );
		printf ( "tt = %d\n", x );

		// speed_t cfgetispeed(const struct termios *termios_p);
		// speed_t cfgetospeed(const struct termios *termios_p);

		speed = cfgetispeed ( &tt );
		printf ( "I speed = %d\n", speed );
		speed = cfgetospeed ( &tt );
		printf ( "O speed = %d\n", speed );

		speed = B9600;
		printf ( "Set speed to: %d\n", speed );
		x = cfsetispeed ( &tt, speed);
		printf ( "set = %d\n", x );
		x = cfsetospeed ( &tt, speed);
		printf ( "set = %d\n", x );

		/* Calling this did the trick */
		x = tcsetattr ( fd, TCSANOW, &tt );
		printf ( "set = %d\n", x );

		speed = cfgetispeed ( &tt );
		printf ( "I speed = %d\n", speed );
		speed = cfgetospeed ( &tt );
		printf ( "O speed = %d\n", speed );

		return fd;
}

void
buf_show ( char *buf, int n )
{
		int i;

		for ( i=0; i<n; i++ ) {
			printf ( " %02x", buf[i] );
		}
		printf ( "\n" );
}

/* Note that upper case A is different from lower case a
 * Upper case sets the averaging for spectra
 * Lower case specifies ascii mode for output
 */
void
set_ascii ( int fd )
{
		int n;
		char buf[BSIZE];

		n = write ( fd, "a\n", 2 );
		printf ( "Write: %d\n", n );

		sleep ( 2 );

		/* We get an 8 byte response -- 
		 * Got: 8
		 * 41 0d 0a 41 43 4b 0d 0a
		 * The echo and the ACK
		 */

		n = read ( fd, buf, BSIZE );
		printf ( "Got: %d\n", n );
		// printf ( "Buf: %02x", buf[0] );
		buf_show ( buf, n );
}

int
get_setting ( int fd, int who )
{
		char buf[BSIZE];
		int n;
		int rv;

		sprintf ( buf, "?%c\n", who );
		write ( fd, buf, 3 );

		sleep ( 2 );

		/* This gets:
		 * Got: 16
		 * 3f 4b 0d 0a 41 43 4b 0d 0a 30 30 30 30 33 0d 0a
		 */

		n = read ( fd, buf, BSIZE );
		printf ( "Got: %d\n", n );
		// printf ( "Buf: %02x", buf[0] );
		buf_show ( buf, n );

		rv = atoi ( &buf[9] );

		return rv;
}

void
save ( char *path, char *buf, int n )
{
		int ofd;

		ofd = open ( path, O_WRONLY | O_TRUNC | O_CREAT, 0644 );
		write ( ofd, buf, n );
		close ( ofd );
}

void
do_scan ( int fd )
{
		int n;
		char buf[BSIZE];
		int empty;
		int num;
		char *p, *q;
		int i;

		printf ( "Begin scan ---\n" );

		n = write ( fd, "S\n", 2 );
		printf ( "Write: %d\n", n );

		empty = 0;
		num = 0;
		p = image;
		for ( ;; ) {
			n = read ( fd, buf, BSIZE );
			if ( n == 0 ) {
				empty++;
			} else {
				if ( n != 1 )
					printf ( "Oops: %d\n", n );
				num += n;
				q = buf;
				for ( i=0; i<n; i++ )
					*p++ = *q++;
				// printf ( "Got: %d %d\n", empty, n );
				// buf_show ( buf, n );
				empty = 0;
				if ( buf[n-1] == '\0' )
					break;
			}
		}

		// 14345 bytes 
		printf ( "Scan gave %d bytes\n", num );
		save ( outfile, image, num );
}

int
main ( int argc, char **argv )
{
		int fd;
		int x;

		fd = setup ( device );

		set_ascii ( fd );
		x = get_setting ( fd, 'K' );
		printf ( "Baud set to %d\n", x );

		do_scan ( fd );

		return 0;
}

/* THE END */
