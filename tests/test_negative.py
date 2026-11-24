import pytest

pytestmark = pytest.mark.negative


@pytest.mark.parametrize("cmd,error", [
    ("NOT_A_COMMAND", '-100,"Command error"'), ("", '-102,"Syntax error"'),
    ("CONF:VOLT:DC ABC", '-102,"Syntax error"'), ("OUTP", '-102,"Syntax error"'),
    ("SOUR:SIM", '-102,"Syntax error"'), ("SOUR:NOISE YES", '-102,"Syntax error"'),
    ("OUTP ON OFF", '-102,"Syntax error"'), ("*RST 1", '-102,"Syntax error"'),
    ("CONF:RES 0", '-222,"Data out of range"'), ("CONF:CURR:DC 10.1", '-222,"Data out of range"'),
    ("SOUR:SIM 1e999", '-222,"Data out of range"'), ("SOUR:SIM NaN", '-102,"Syntax error"'),
])
def test_reject_write(dmm, cmd, error):
    assert dmm.execute(cmd) is None
    assert dmm.execute("SYST:ERR?") == error
    assert dmm.execute("CONF?") == "VOLT:DC,100.0"
    assert dmm.execute("OUTP?") == "0"
    assert dmm.instrument.simulated_signal == 0.0
    assert dmm.execute("SYST:ERR?") == '0,"No error"'


def test_unknown_query(dmm):
    assert dmm.execute("FOO?") == '-100,"Command error"'
    assert dmm.execute("SYST:ERR?") == '-100,"Command error"'


def test_disabled(dmm):
    dmm.execute("SOUR:SIM 200")
    assert dmm.execute("MEAS:VOLT:DC?") == "0.000"
    assert dmm.execute("SYST:ERR?") == '0,"No error"'


def test_conflict(dmm):
    dmm.execute("OUTP ON")
    assert dmm.execute("MEAS:RES?") == '-221,"Settings conflict"'
    assert dmm.execute("SYST:ERR?") == '-221,"Settings conflict"'
