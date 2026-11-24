"""Isolated instrument and loopback fixtures."""
import random

import pytest

from dmm_simqa.client import SCPIClient
from dmm_simqa.instrument import VirtualDMM
from dmm_simqa.scpi_parser import SCPIParser
from dmm_simqa.server import SCPIServer


@pytest.fixture
def dmm():
    return SCPIParser(VirtualDMM(random.Random(34401)))


@pytest.fixture(scope="module")
def tcp_server():
    server = SCPIServer(port=0)
    server.start()
    try:
        yield server
    finally:
        server.stop()


@pytest.fixture
def tcp_client(tcp_server):
    with SCPIClient(tcp_server.host, tcp_server.port) as client:
        client.write("*RST")
        assert client.query("OUTP?") == "0"
        yield client
