import pytest

pytestmark = pytest.mark.boundary


@pytest.mark.parametrize("mode,signal,expected", [
    ("VOLT:DC", "0", "0.000"), ("VOLT:DC", "0.001", "0.001"),
    ("VOLT:DC", "100.0", "100.000"), ("CURR:DC", "10.0", "10.000"),
    ("RES", "1e6", "1000000.0"), ("CURR:DC", "0.001", "0.001"),
    ("RES", "0.001", "0.0"), ("RES", "0.1", "0.1"),
])
def test_valid_boundary(dmm, mode, signal, expected):
    for cmd in (f"CONF:{mode}", f"SOUR:SIM {signal}", "OUTP ON", "SOUR:NOISE OFF"):
        dmm.execute(cmd)
    assert dmm.execute(f"MEAS:{mode}?") == expected
    assert dmm.execute("SYST:ERR?") == '0,"No error"'


@pytest.mark.parametrize("mode,limit,signal", [
    ("VOLT:DC", "100", "100.001"), ("VOLT:DC", "100", "-0.001"),
    ("CURR:DC", "10", "10.001"), ("RES", "1e6", "1000000.1"),
    ("VOLT:DC", "0.1", "0.10001"),
])
def test_overload(dmm, mode, limit, signal):
    for cmd in (f"CONF:{mode} {limit}", "OUTP ON", f"SOUR:SIM {signal}"):
        dmm.execute(cmd)
    assert dmm.execute(f"MEAS:{mode}?") == "9.9E+37"
    assert dmm.execute("SYST:ERR?") == '-222,"Data out of range"'
    assert dmm.execute("SYST:ERR?") == '0,"No error"'
