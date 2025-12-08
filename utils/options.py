# utils/options.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Options:
    n_avg: int = 200
    simulate: bool = False
    dc_set_voltage: bool = False
