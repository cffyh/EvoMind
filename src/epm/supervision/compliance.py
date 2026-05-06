"""Compliance — 申报价格上下限 + 时间窗口校验.

Per v2.0 §3.3.6: hardcoded, both Agent and humans must pass through it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time

import numpy as np

from epm.config import MarketRules
from .risk_guard import GuardViolation


@dataclass
class ComplianceChecker:
    rules: MarketRules
    declaration_window_open: time = time(0, 0)    # D-1 9:00 typical
    declaration_window_close: time = time(15, 0)  # D-1 15:00 typical

    def check_prices(self, p_da: np.ndarray | None) -> None:
        if p_da is None:
            return  # quantity-only declaration mode
        floor, cap = self.rules.price_floor, self.rules.price_cap
        if not self.rules.allow_negative_price and (p_da < 0).any():
            raise GuardViolation("negative declared price not allowed in this province")
        if (p_da < floor).any() or (p_da > cap).any():
            raise GuardViolation(f"declared price outside [{floor}, {cap}] 元/MWh")

    def check_monotonic(self, p_da: np.ndarray | None) -> None:
        """量价曲线单调性（带价申报市场）— v2.0 §4.1.3."""
        if p_da is None:
            return
        if (np.diff(p_da) < 0).any():
            raise GuardViolation("declared price curve must be monotone non-decreasing in quantity")

    def check_window(self, now: datetime) -> None:
        t = now.time()
        if not (self.declaration_window_open <= t <= self.declaration_window_close):
            raise GuardViolation(
                f"current time {t} outside declaration window "
                f"[{self.declaration_window_open}, {self.declaration_window_close}]"
            )
