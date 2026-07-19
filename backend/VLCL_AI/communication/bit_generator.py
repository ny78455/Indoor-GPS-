# bit_generator.py
import numpy as np
from VLCL_AI.communication.exceptions import VLCLCommunicationError

class BitGenerator:
    """Generates random information bits for physical layer transmission."""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate(self, num_bits: int) -> np.ndarray:
        """Generates random bits (0 or 1) of dtype uint8."""
        if num_bits <= 0:
            raise VLCLCommunicationError("Number of bits must be greater than zero.")
        return self.rng.integers(0, 2, size=num_bits, dtype=np.uint8)

    def generate_seeded(self, num_bits: int, seed: int) -> np.ndarray:
        """Generates seeded random bits for reproducible testing."""
        if num_bits <= 0:
            raise VLCLCommunicationError("Number of bits must be greater than zero.")
        temp_rng = np.random.default_rng(seed)
        return temp_rng.integers(0, 2, size=num_bits, dtype=np.uint8)
