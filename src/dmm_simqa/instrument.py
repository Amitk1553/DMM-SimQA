"""State and measurement model for one virtual bench instrument."""
import math
import random

from .config import ERRORS, MODES, OVERLOAD
from .exceptions import OutOfRangeError, SettingsConflictError


class VirtualDMM:
    """Model a unipolar meter with selectable input range and output gate."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng if rng is not None else random.Random()
        self.error_queue: list[str] = []
        self.reset()

    def reset(self) -> None:
        """Restore power-on defaults including the error register."""
        self.mode = "VOLT:DC"
        self.range_limit = MODES[self.mode].maximum
        self.output_enabled = False
        self.simulated_signal = 0.0
        self.noise_enabled = True
        self.error_queue.clear()

    def configure(self, mode: str, limit: float | None) -> None:
        """Select a function and full scale, committing both together."""
        spec = MODES[mode]
        limit = spec.maximum if limit is None else limit
        if not spec.minimum < limit <= spec.maximum:
            raise OutOfRangeError
        self.mode, self.range_limit = mode, limit

    def set_signal(self, value: float) -> None:
        """Accept finite inputs, including signals that will overload."""
        if not math.isfinite(value):
            raise OutOfRangeError
        self.simulated_signal = value

    def measure(self, mode: str) -> str:
        """Test true input for overload before adding noise and rounding."""
        spec = MODES[mode]
        if not self.output_enabled:
            return spec.format(0.0)
        if mode != self.mode:
            raise SettingsConflictError
        value = self.simulated_signal
        if not spec.minimum <= value <= self.range_limit:
            self.error_queue.append(ERRORS[-222])
            return OVERLOAD
        if self.noise_enabled:
            value += self.rng.gauss(0.0, spec.noise_std)
        return spec.format(max(spec.minimum, min(self.range_limit, value)))
