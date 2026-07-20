# exceptions.py

class LocalizationError(Exception):
    """Base class for all localization-related exceptions."""
    pass

class ConfigurationError(LocalizationError):
    """Raised when the frequency plan or mapping is invalid."""
    pass

class SignalError(LocalizationError):
    """Raised when there are issues with the received localization signals (e.g. low SNR, blockage)."""
    pass

class SolverError(LocalizationError):
    """Raised when the position solver fails to converge or produces invalid results."""
    pass

class CalibrationError(LocalizationError):
    """Raised when calibration parameters are invalid or calibration fails."""
    pass
