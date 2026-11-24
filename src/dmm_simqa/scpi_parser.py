"""Line-oriented SCPI subset shared by local and socket clients."""
import logging
import re
from threading import Lock

from .config import ERRORS, IDENTITY, MODES
from .exceptions import DMMError, SCPISyntaxError
from .instrument import VirtualDMM

LOG = logging.getLogger(__name__)
ALIASES = dict(CONFIGURE="CONF", VOLTAGE="VOLT", CURRENT="CURR", RESISTANCE="RES",
               OUTPUT="OUTP", SOURCE="SOUR", SIMULATE="SIM", MEASURE="MEAS",
               SYSTEM="SYST", ERROR="ERR")
NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?")
CONFIG = {"CONF:" + mode: mode for mode in MODES}
MEASURE = {"MEAS:" + mode + "?": mode for mode in MODES}


def number(token: str) -> float:
    """Parse a decimal SCPI numeric parameter."""
    if not NUMBER.fullmatch(token):
        raise SCPISyntaxError
    return float(token)


class SCPIParser:
    """Execute complete commands atomically on one instrument."""

    def __init__(self, instrument: VirtualDMM) -> None:
        self.instrument = instrument
        self._lock = Lock()

    def execute(self, line: str) -> str | None:
        """Return a query response, or None for a write, and queue errors."""
        with self._lock:
            fields = line.strip().upper().split()
            header = fields[0].removeprefix(":") if fields else ""
            query = header.endswith("?")
            parts = header.removesuffix("?").split(":")
            header = ":".join(ALIASES.get(word, word) for word in parts)
            if query:
                header += "?"
            try:
                return self._dispatch(header, fields[1:])
            except DMMError as exc:
                error = ERRORS[exc.code]
                self.instrument.error_queue.append(error)
                LOG.debug("SCPI error %s on %.80r", error, header)
                return error if query else None

    def _dispatch(self, header: str, args: list[str]) -> str | None:
        meter = self.instrument
        if not header or len(args) > 1:
            raise SCPISyntaxError
        if header in CONFIG:
            meter.configure(CONFIG[header], number(args[0]) if args else None)
        elif header in ("OUTP", "SOUR:NOISE", "SOUR:SIM"):
            if not args:
                raise SCPISyntaxError
            if header == "SOUR:SIM":
                meter.set_signal(number(args[0]))
            elif args[0] not in ("ON", "OFF"):
                raise SCPISyntaxError
            elif header == "OUTP":
                meter.output_enabled = args[0] == "ON"
            else:
                meter.noise_enabled = args[0] == "ON"
        elif args:
            raise SCPISyntaxError
        elif header == "*IDN?":
            return IDENTITY
        elif header == "*RST":
            meter.reset()
        elif header == "*CLS":
            meter.error_queue.clear()
        elif header == "CONF?":
            return f"{meter.mode},{meter.range_limit}"
        elif header == "OUTP?":
            return str(int(meter.output_enabled))
        elif header == "SYST:ERR?":
            return meter.error_queue.pop(0) if meter.error_queue else ERRORS[0]
        elif header in MEASURE:
            return meter.measure(MEASURE[header])
        else:
            raise DMMError
        return None
