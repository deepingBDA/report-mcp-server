from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class PeriodSummary:
    site: str
    curr_total: Optional[int]
    prev_total: Optional[int]
    weekday_delta_pct: Optional[float]
    weekend_delta_pct: Optional[float]
    total_delta_pct: Optional[float]


def to_pct_series(values: List[int]) -> List[float]:
    pct: List[float] = []
    for i in range(1, len(values)):
        prev = values[i - 1]
        curr = values[i]
        pct.append(0.0 if prev == 0 else (curr - prev) / prev * 100.0)
    return pct

