# exceptions.py
class VLCLCommunicationError(Exception):
    """Base exception for VLCL communication modules."""
    pass

class ModulationError(VLCLCommunicationError):
    """Exception raised for QAM/modulation errors."""
    pass

class OFDMError(VLCLCommunicationError):
    """Exception raised for OFDM grid, framing or transform errors."""
    pass

class HardwareError(VLCLCommunicationError):
    """Exception raised for physical device limitation violations (clipping, DAC/ADC)."""
    pass
