"""Tests for CRV FEB that can be done with just a bare board."""
import pytest
import sockexpect
import re
from warnings import warn

@pytest.fixture(scope="session")
def feb_connection():
    """A pytest test fixture that provides a stable connection to the FEB.
    Assumes that FEB has address 172.16.10.10 and port 5002.
    """
    # pylint: disable=import-outside-toplevel
    import socket
    ip, port = ('172.16.10.10', 5002)
    sock = socket.socket()
    sock.connect((ip, port))
    sock.settimeout(3.0)
    yield sock
    sock.close()

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
    s.expect(br'Temp_C.*\n')
    print(s.before+s.after)
    s.after.clear()

def test_SD(feb_connection):
    s = sockexpect.SockExpect(feb_connection)
    feb_connection.settimeout(45.0) # FIXME! Change to 45 s
    nfailures = 0
    for ifpga in range(1,5):
        s.before.clear()
        s.after.clear()
        s.sendline(bytes(f'SD {ifpga}', 'ascii'))
        s.expect(br'Test.*\n')
        print(f'SD {ifpga}: {s.before+s.after}')
        if b'Tested Okay' not in s.after:
            warn(f'FPGA {ifpga} failed SD test')
            nfailures += 1
    assert nfailures == 0


    
