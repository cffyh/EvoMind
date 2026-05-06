"""Realtime adjustment agent — v2.0 §3.3.5.

MPC rolling optimizer running every 15 minutes. Trigger condition:
4-hour rolling forecast shows day-ahead deviation > ±1.5%
(< the罚款 threshold).

Last line of defense for the 偏差率指标 — keep this code path
deliberately simple and well-tested.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from epm.config import MarketRules


@dataclass
class RealtimeContext:
    """Snapshot of the day so far + 4-hour forecast going forward."""
    rules: MarketRules
    declared_q: np.ndarray            # (T,) original day-ahead declaration
    realized_q_so_far: np.ndarray     # (t,) actual procurement up to now
    realized_load_so_far: np.ndarray  # (t,) actual load up to now
    forecast_load_4h: np.ndarray      # (k,) 4-hour load forecast quantiles
    forecast_price_rt_4h: np.ndarray  # (k,) 4-hour realtime price forecast


def should_trigger(ctx: RealtimeContext, threshold: float = 0.015) -> bool:
    """Trigger condition per v2.0 §3.3.5: rolling deviation > ±1.5%."""
    if ctx.realized_load_so_far.size == 0:
        return False
    cum_actual = float(np.sum(ctx.realized_load_so_far))
    cum_declared = float(np.sum(ctx.declared_q[: ctx.realized_load_so_far.size]))
    if cum_actual == 0:
        return False
    deviation = (cum_declared - cum_actual) / cum_actual
    return abs(deviation) > threshold


def adjust(ctx: RealtimeContext) -> np.ndarray:  # pragma: no cover — TODO M5
    """Roll out a 4-hour MPC, return realtime quantity adjustments per period.

    Stub: M5 deliverable. Until then, callers fall back to no-adjustment.
    """
    raise NotImplementedError("realtime MPC — see v2.0 §3.3.5")
