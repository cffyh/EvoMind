"""Action space — v2.0 §4.5.3.

Continuous: a = (α^q, α^p, β^p) ∈ [0.85, 1.15] × [0.9, 1.1] × [0, 0.5]
Discretized: 7 × 5 × 3 = 105 actions for FQI-GBM.

At execution time (every 15 min):
    opt_q_τ = α^q · L̂_τ                        (量的偏移因子 × 负荷预测)
    opt_p_τ = α^p · π̂_τ + β^p · σ̂_τ            (价的基础 + 风险溢价)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


ACTION_BOUNDS = {
    "alpha_q": (0.85, 1.15),
    "alpha_p": (0.90, 1.10),
    "beta_p": (0.00, 0.50),
}

_ALPHA_Q_GRID = np.linspace(*ACTION_BOUNDS["alpha_q"], 7)
_ALPHA_P_GRID = np.linspace(*ACTION_BOUNDS["alpha_p"], 5)
_BETA_P_GRID = np.linspace(*ACTION_BOUNDS["beta_p"], 3)


@dataclass(frozen=True)
class Action:
    alpha_q: float
    alpha_p: float
    beta_p: float

    def declare_quantity(self, load_forecast: float) -> float:
        return float(self.alpha_q * load_forecast)

    def declare_price(self, price_forecast: float, price_vol_forecast: float) -> float:
        return float(self.alpha_p * price_forecast + self.beta_p * price_vol_forecast)


def _build_action_space() -> list[Action]:
    space = []
    for aq in _ALPHA_Q_GRID:
        for ap in _ALPHA_P_GRID:
            for bp in _BETA_P_GRID:
                space.append(Action(float(aq), float(ap), float(bp)))
    return space


ACTION_SPACE: list[Action] = _build_action_space()


def decode_action(idx: int) -> Action:
    return ACTION_SPACE[idx]
