import pytest

pytestmark = pytest.mark.smoke


def test_identity(dmm):
    assert dmm.execute("*IDN?") == "SimQA-Labs,DMM-34401A,SQ001234,1.2.0"


def test_reset_defaults(dmm):
    for cmd in ("CONF:RES 10", "OUTP ON", "SOUR:SIM 4", "SOUR:NOISE OFF", "BAD", "*RST"):
        dmm.execute(cmd)
    assert dmm.execute("CONF?") == "VOLT:DC,100.0"
    assert dmm.execute("OUTP?") == "0"
    assert dmm.instrument.simulated_signal == 0.0
    assert dmm.instrument.noise_enabled
    assert dmm.execute("SYST:ERR?") == '0,"No error"'


def test_empty_queue(dmm):
    assert dmm.execute("SYST:ERR?") == '0,"No error"'


def test_output(dmm):
    for setting, state in [("ON", "1"), ("OFF", "0")]:
        assert dmm.execute(f"OUTP {setting}") is None
        assert dmm.execute("OUTP?") == state
