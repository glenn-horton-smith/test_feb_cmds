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
        self.after = bytearray()
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
        Data is read in chunks of size up to self.maxchunksize
        before being checked for a regexp match, so the buffer may
        contain data send by the server after the regexp match.
        Raises an exception on timeout error or socket close.
        On success, self.before will be equal to data received up
        to the start of the matched expression, and self.after
        will be equal to the matched expression and any data received
        afterwards. The of self.after is retained between calls, and
        matching is applied to data previously received.
        On failure, self.after will be equal to all
        data received appended to the value of self.after on entry.
        Both self.after and self.before are bytearray objects.
        """
        if isinstance(regexp, bytes):
            regexp = re.compile(regexp)
        while True:
            alen0 = len(self.after)
            if alen0 > 0:
                m = regexp.search(self.after)
                if m is not None:
                    break
            if alen0 > self.maxbuffsize - self.maxchunksize:
                del self.after[:self.maxchunksize]
                alen0 = len(self.maxchunksize)
            try:
                self.after += self.s.recv(self.maxchunksize)
            except socket.timeout:
                raise Exception(f"sockexpect.expect: timed out waiting"
                                f" for {regexp}, received {self.after}")
            if len(self.after) == alen0:
                raise Exception(f"sockexpect.expect: did not find "
                                f"{regexp} in response {self.after}")
        istart = m.start()
        self.before = self.after[:istart]
        del self.after[:istart]
