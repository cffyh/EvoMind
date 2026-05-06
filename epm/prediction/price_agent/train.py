"""Day-ahead + realtime price forecasting — joint distribution.

Baseline per v2.0 §3.3.2: Chen-Wang (2015) lattice framework with
stochastic volatility. AutoResearch may iterate features, volatility
model (GARCH/SV/Heston), jump parameterization, and ensemble weights.
Primary metric is **CRPS / Pinball Loss** — RMSE is explicitly forbidden
as a primary metric.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


QUANTILES: tuple[float, ...] = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)


@dataclass
class PriceModel:
    """Holds DA + RT quantile heads + the SV parameter snapshot."""
    da_estimators: dict[float, Any]
    rt_estimators: dict[float, Any]
    feature_cols: list[str]
    sv_params: dict          # {(province, month, macro_period): (mu, kappa, theta, delta)}
    meta: dict


def train(features: pd.DataFrame, da_target: str = "da_settle", rt_target: str = "rt_settle") -> PriceModel:
    """Fit DA + RT quantile heads on the merged feature frame.

    Stub: implementer plugs in LightGBM with quantile loss / NN quantile head /
    SV-ensemble per v2.0 §3.3.2.
    """
    raise NotImplementedError("price_agent.train: see program.md priorities")
