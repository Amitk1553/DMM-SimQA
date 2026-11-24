import pytest

pytestmark = [pytest.mark.functional, pytest.mark.regression]


@pytest.mark.parametrize("mode,expected", [("VOLT:DC", "2.346"), ("CURR:DC", "2.346"), ("RES", "2.3")])
def test_deterministic(dmm, mode, expected):
    for cmd in (f"CONF:{mode} 5", "OUTP ON", "SOUR:NOISE OFF", "SOUR:SIM 2.3456"):
        dmm.execute(cmd)
    for _ in range(2):
        assert dmm.execute(f"MEAS:{mode}?") == expected
    assert dmm.execute("CONF?") == f"{mode},5.0"


@pytest.mark.parametrize("mode,sigma", [("VOLT:DC", 0.005), ("CURR:DC", 0.002), ("RES", 0.5)])
def test_noise(dmm, mode, sigma):
    from statistics import mean, stdev

    for cmd in (f"CONF:{mode}", "OUTP ON", "SOUR:SIM 5", "SOUR:NOISE ON"):
        dmm.execute(cmd)
    samples = [float(dmm.execute(f"MEAS:{mode}?")) for _ in range(400)]
    assert mean(samples) == pytest.approx(5, abs=sigma * 0.2)
    assert stdev(samples) == pytest.approx(sigma, rel=0.15)


@pytest.mark.parametrize("function,short", [("voltage:dc", "VOLT:DC"), ("Current:DC", "CURR:DC"),
                                            ("Resistance", "RES")])
def test_long_headers(dmm, function, short):
    dmm.execute(f"  :configure:{function}   2e0  \r\n")
    assert dmm.execute(" configure? ") == f"{short},2.0"
    for cmd in ("output on", "source:simulate 1", "source:noise off"):
        dmm.execute(cmd)
    assert float(dmm.execute(f"measure:{function}?\r\n")) == 1
    assert dmm.execute("system:error?") == '0,"No error"'


def test_clear(dmm):
    for cmd in ("INVALID", "OUTP", "*CLS"):
        dmm.execute(cmd)
    assert dmm.execute("SYST:ERR?") == '0,"No error"'


def test_fifo(dmm):
    for cmd in ("BAD", "OUTP", "CONF:RES -1"):
        dmm.execute(cmd)
    assert [dmm.execute("SYST:ERR?") for _ in range(4)] == [
        '-100,"Command error"', '-102,"Syntax error"', '-222,"Data out of range"', '0,"No error"']


def test_default_range(dmm):
    dmm.execute("CONF:RES 5")
    dmm.execute("CONF:RES")
    assert dmm.execute("CONF?") == "RES,1000000.0"
