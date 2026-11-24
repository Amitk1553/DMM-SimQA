"""Domain failures translated to instrument error responses by the parser."""


class DMMError(Exception):
    """Unrecognized command header."""

    code = -100


class SCPISyntaxError(DMMError):
    """Invalid argument syntax or arity."""

    code = -102


class OutOfRangeError(DMMError):
    """Numeric value outside supported limits."""

    code = -222


class SettingsConflictError(DMMError):
    """Measurement requested in a different mode."""

    code = -221
