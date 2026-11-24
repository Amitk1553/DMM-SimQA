from concurrent.futures import ThreadPoolExecutor
import socket
from threading import Barrier

import pytest

from dmm_simqa.client import SCPIClient
from dmm_simqa.server import SCPIServer

pytestmark = pytest.mark.integration


def test_tcp_cycle(tcp_client):
    for command in ("CONF:CURR:DC 2", "SOUR:SIM 1.234", "OUTP ON", "SOUR:NOISE OFF"):
        tcp_client.write(command)
    assert tcp_client.query("MEAS:CURR:DC?") == "1.234"
    assert tcp_client.query("CONF?") == "CURR:DC,2.0"


def test_concurrent_clients(tcp_server, tcp_client):
    ready = Barrier(4)
    def worker(i):
        with SCPIClient(port=tcp_server.port) as client:
            ready.wait(timeout=5)
            client.write(f"BAD{i}")
            assert client.query("OUTP?") == "0"

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(worker, range(4)))
    assert [tcp_client.query("SYST:ERR?") for _ in range(4)] == ['-100,"Command error"'] * 4
    assert tcp_client.query("SYST:ERR?") == '0,"No error"'


def test_partial_disconnect(tcp_server, tcp_client):
    with socket.create_connection((tcp_server.host, tcp_server.port), timeout=2) as sock:
        sock.sendall(b"OUTP ON")
        sock.shutdown(socket.SHUT_WR)
        assert sock.recv(1) == b""
    assert tcp_client.query("OUTP?") == "0"


def test_timeout(tcp_server, tcp_client):
    with SCPIClient(port=tcp_server.port, timeout=0.1) as client:
        with pytest.raises(TimeoutError):
            client.query("*CLS")  # A write has no reply.
        with pytest.raises(RuntimeError):
            client.write("OUTP ON")
    assert tcp_client.query("OUTP?") == "0"


def test_stop_idle_peer():
    server = SCPIServer(port=0)
    server.start()
    try:
        server.start()
        with SCPIClient(port=server.port) as client:
            assert client.query("OUTP?") == "0"
            server.stop()
            with pytest.raises(OSError):
                client.query("OUTP?")
    finally:
        server.stop()


def test_framing(tcp_server, tcp_client):
    with socket.create_connection((tcp_server.host, tcp_server.port), timeout=2) as sock:
        with sock.makefile("rb") as reader:
            sock.sendall(b"OU")
            sock.sendall(b"TP ON\r\nOUTP?\n\xff\nSYST:ERR?\n")
            assert reader.readline() == b"1\n"
            assert reader.readline() == b'-102,"Syntax error"\n'
            sock.sendall(b"X" * 4097)
            assert reader.read(1) == b""


def test_client_guards(tcp_client):
    with pytest.raises(RuntimeError):
        tcp_client.__enter__()
    with pytest.raises(ValueError):
        tcp_client.write("OUTP ON\n*RST")
    assert tcp_client.query("OUTP?") == "0"
