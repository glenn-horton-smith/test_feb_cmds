"""Tests for CRV FEB that can be done with just a bare board."""
import pytest
import sockexpect
import re
from warnings import warn

@pytest.fixture(scope="session")
def feb_connection():
    """Make a test fixture for pytest to reuse the same feb_connnection
    for all tests."""
    # pylint: disable=import-outside-toplevel
    sock = make_feb_socket()
    yield sock
    sock.close()

def make_feb_socket():
    """Make connection to the FEB.
    Assumes that FEB has address 172.16.10.10 and port 5002.
    """
    import socket
    ip, port = ('172.16.10.10', 5002)
    sock = socket.socket()
    sock.connect((ip, port))
    sock.settimeout(3.0)
    return sock

def test_ID(feb_connection): # pylint: disable=redefined-outer-name
    s = sockexpect.SockExpect(feb_connection)
    s.send(b'ID\r\n')
    s.expect(br'Serial Number.*\n')
    print(s.before)
    print(s.after)
    match = re.search( br'uC ECC ReBoots : 0\r\n', s.before)
    assert match != None, "Failed 0 uB ECC ReBoots test"
    match = re.search( br'FPGA ECC Errors: 0\r\n', s.before)
    assert match != None, "Failed 0 FPGA ECC Errors test"
    

def test_ADC(feb_connection): # pylint: disable=redefined-outer-name
    s = sockexpect.SockExpect(feb_connection)
    s.send(b'ADC\r\n')
    s.expect(br'1.2v_Pos *')
    print("Before: " + repr(s.before))
    print("Match: " + repr(s.match))
    print("data: " + repr(s.data))
    s.expect(br'-*[0-9.]+')
    print("Before: " + repr(s.before))
    print("Match: " + repr(s.match))
    v = float(s.match.group(0))
    # TODO: compare v to expected values 1.2
    # TODO: repeat above for 1.8v_Pos, etc.....
    print(" *** The voltage is """, v, " !!!!")
    print("data: " + repr(s.data))
    s.expect(br'Temp_C.*\n')
    print("Before: " + repr(s.before))
    print("Match: " + repr(s.match))
    print("data: " + repr(s.data))
    s.data.clear()

def test_SD(feb_connection):
    s = sockexpect.SockExpect(feb_connection)
    feb_connection.settimeout(45.0) # FIXME! Change to 45 s
    nfailures = 0
    for ifpga in range(1,5):
        s.before.clear()
        s.data.clear()
        s.sendline(bytes(f'SD {ifpga}', 'ascii'))
        s.expect(br'Test.*\n')
        print(f'SD {ifpga}: Before: {s.before}, Data: {s.data}')
        if b'Tested Okay' not in s.data:
            warn(f'FPGA {ifpga} failed SD test')
            nfailures += 1
    assert nfailures == 0


    
