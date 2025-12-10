# utils/options.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from utils.units import u


@dataclass
class Options:
    n_avg: int = 200
    dc_set_voltage: bool = False
    plot: bool = True
    save: bool = False
    update_args: bool = False
    simulate: bool = False
    simulate_duration: float = 100 * u.us
    state_discrimination: bool = False
    active_reset: bool = False
