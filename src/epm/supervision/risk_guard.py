"""Hard-coded risk caps — v2.0 §3.3.6.

Every decision must pass through `RiskGuard.check`. A guard violation
short-circuits the daily loop and triggers the human review闸门.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from epm.config import MarketRules
from epm.risk.var_cvar import conditional_value_at_risk


class GuardViolation(Exception):
    """Raised when a hard risk cap is breached."""


@dataclass
class RiskGuard:
    rules: MarketRules
    cvar_loss_limit: float                 # 元
    daily_spend_cap_yuan: float | None = None
    period_position_cap_mwh: float | None = None

    def check(
        self,
        q_da: np.ndarray,
        price_forecast: np.ndarray,
        scenario_losses: np.ndarray,
    ) -> None:
        """Hard checks. All caps are CEILINGS — exceeding any one is a violation."""
        if q_da.shape != price_forecast.shape:
            raise ValueError("q_da and price_forecast must have the same shape")

        # 单时段最大头寸
        if self.period_position_cap_mwh is not None:
            peak = float(np.max(np.abs(q_da)))
            if peak > self.period_position_cap_mwh:
                raise GuardViolation(
                    f"period position {peak:.2f} MWh exceeds cap "
                    f"{self.period_position_cap_mwh:.2f}"
                )

        # 单日最大现货采购金额
        if self.daily_spend_cap_yuan is not None:
            daily_spend = float(np.sum(np.maximum(q_da, 0) * price_forecast))
            if daily_spend > self.daily_spend_cap_yuan:
                raise GuardViolation(
                    f"daily spend {daily_spend:.0f} 元 exceeds cap "
                    f"{self.daily_spend_cap_yuan:.0f}"
                )

        # CVaR 上限
        cvar = conditional_value_at_risk(scenario_losses, self.rules.cvar_alpha)
        if cvar > self.cvar_loss_limit:
            raise GuardViolation(
                f"CVaR_{self.rules.cvar_alpha:.2f} loss {cvar:.0f} 元 exceeds cap "
                f"{self.cvar_loss_limit:.0f}"
            )
