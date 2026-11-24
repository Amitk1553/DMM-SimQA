"""Instrument identity, measurement characteristics and SCPI error vocabulary."""
from dataclasses import dataclass

MANUFACTURER = "SimQA-Labs"
MODEL = "DMM-34401A"
SERIAL = "SQ001234"
FIRMWARE = "1.2.0"
IDENTITY = ",".join((MANUFACTURER, MODEL, SERIAL, FIRMWARE))
OVERLOAD = "9.9E+37"


@dataclass(frozen=True)
class MeasurementSpec:
    """Unipolar measurement limits and Gaussian noise in engineering units."""

    minimum: float
    maximum: float
    resolution: float
    noise_std: float

    def format(self, value: float) -> str:
        """Use the decimal places specified by the instrument resolution."""
        places = len(str(self.resolution).partition(".")[2])
        return f"{value:.{places}f}"


MODES = {
    "VOLT:DC": MeasurementSpec(0.0, 100.0, 0.001, 0.005),
    "CURR:DC": MeasurementSpec(0.0, 10.0, 0.001, 0.002),
    "RES": MeasurementSpec(0.0, 1_000_000.0, 0.1, 0.5),
}
ERRORS = {
    0: '0,"No error"',
    -100: '-100,"Command error"',
    -102: '-102,"Syntax error"',
    -222: '-222,"Data out of range"',
    -221: '-221,"Settings conflict"',
}
