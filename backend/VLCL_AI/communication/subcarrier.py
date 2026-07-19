# subcarrier.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class SubcarrierPurpose(str, Enum):
    COMMUNICATION = "COMMUNICATION"
    LOCALIZATION_RESERVED = "LOCALIZATION_RESERVED"
    PILOT = "PILOT"
    GUARD = "GUARD"
    DC = "DC"
    UNUSED = "UNUSED"

@dataclass
class Subcarrier:
    index: int
    center_frequency: float
    bandwidth: float
    power: float = 1.0
    modulation_order: int = 16
    assigned_user: Optional[int] = None
    active: bool = True
    pilot: bool = False
    reserved: bool = False
    purpose: SubcarrierPurpose = SubcarrierPurpose.COMMUNICATION
