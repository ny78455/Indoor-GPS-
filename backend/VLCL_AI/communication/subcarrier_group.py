# subcarrier_group.py
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SubcarrierGroup:
    group_id: int
    name: str
    subcarrier_indices: List[int]
    assigned_user: Optional[int] = None
    modulation_order: int = 16
    power_allocation: float = 1.0
