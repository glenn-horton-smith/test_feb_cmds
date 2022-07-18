#!/usr/bin/env python
"""Provides expect/pexpect style functionality for sockets."""
# -*- coding: utf-8 -*-
#
#  sockexpect.py
#
#  Copyright 2020 Glenn A Horton-Smith <gahs@phys.ksu.edu>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import typing
import socket
import re
from warnings import warn

DEFAULT_TIMEOUT = 1.0
DEFAULT_CHUNKSIZE = 4096
DEFAULT_MAXBUFFSIZE = 4*DEFAULT_CHUNKSIZE

class SockExpect:
    """Provides expect/pexpect style functionality for sockets."""

    def __init__(self, s: socket.socket, eol: bytes = b'\r\n'):
        """Required parameters:
            s: a socket object. A timeout must be set for the expect() function
               to work properly. If s.gettimeout() == None, it will be set to DEFAULT_TIMEOUT.
           Optional parameter:
            eol: bytes to use for end of line in sendline().
        """
        self.s = s
        self.eol = eol
        self.before = bytearray()
        self.match = None
        self.data = bytearray()
        self.maxchunksize = DEFAULT_CHUNKSIZE
        self.maxbuffsize = DEFAULT_MAXBUFFSIZE
        if self.s.gettimeout() is None:
            self.s.settimeout(DEFAULT_TIMEOUT)
            warn(f"SockExpect(): changed socket timeout from None to {DEFAULT_TIMEOUT} s.")

    def send(self, msg: bytes):
        """Send raw bytes to socket."""
        self.s.send(msg)

    def sendline(self, line: bytes):
        """Send raw bytes to socket terminated by self.eol."""
        self.s.send(line + self.eol)

    def expect(self, regexp: typing.Union[bytes, re.Pattern]):
        """Receive and save data from socket until the given regexp
        is matched, a timeout occurs, or the socket is closed.
        
        Keeps bytes read before the match, the match itself, and 
        all bytes read in `before`, `match`,
        and `data`, respectively.
        
        Data is read in chunks of size up to self.maxchunksize
        before being checked for a regexp match, so the buffer may
        contain data send by the server after the regexp match.
        
        Raises an exception on timeout error or socket close.
        
        On success, self.before will be equal to data received up
        to the start of the matched expression, self.match will contain
        the results of the match, and self.data will be equal to 
        any data received.
        
        The value of self.data is retained between calls, and
        matching is applied to data previously received after discarding
        data up to the end of the last match.
        The value of self.before is reset during each call.
        
        On failure, self.data will be equal to all
        data received appended to the value of self.data on entry.
        
        Both self.data and self.before are bytearray objects.
        self.match is a re.Match object.
        """
        if isinstance(regexp, bytes):
            regexp = re.compile(regexp)
        if self.match is not None:
            del self.data[:self.match.end()]
        while True:
            alen0 = len(self.data)
            if alen0 > 0:
                m = regexp.search(self.data)
                if m is not None:
                    break
            if alen0 > self.maxbuffsize - self.maxchunksize:
                del self.data[:self.maxchunksize]
                alen0 = len(self.maxchunksize)
            try:
                self.data += self.s.recv(self.maxchunksize)
            except socket.timeout:
                raise Exception(f"sockexpect.expect: timed out waiting"
                                f" for {regexp}, received {self.data}")
            if len(self.data) == alen0:
                raise Exception(f"sockexpect.expect: did not find "
                                f"{regexp} in response {self.data}")
        istart = m.start()
        self.before = self.data[:istart]
        self.match = m
