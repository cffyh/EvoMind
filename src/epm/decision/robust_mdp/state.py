"""25–30 维状态空间 — v2.0 §4.5.2 + 附录 D `build_state`.

Four feature groups:
  A. Time features (4)
  B. Cumulative state (3)
  C. Current market observation (8)
  D. Forecast distribution (8)
  E. Second-order interactions (3+)
"""
from __future__ import annotations

from typing import Mapping

import numpy as np


STATE_DIM = 26  # 4 + 3 + 8 + 8 + 3


def build_state(
    market_obs: Mapping,
    forecast: Mapping,
    cumulative: Mapping,
    time_info: Mapping,
) -> np.ndarray:
    """Pack heterogeneous observations into a fixed-shape state vector."""
    return np.array(
        [
            # A. Time (4)
            time_info["t_index"],
            time_info["day_of_week"],
            time_info["is_holiday"],
            time_info["days_to_month_end"],
            # B. Cumulative (3)
            cumulative["deviation_pct"],
            cumulative["cost_vs_budget"],
            cumulative["remaining_lt_quota"],
            # C. Market obs (8)
            market_obs["spot_price_avg"],
            market_obs["spot_price_volatility"],
            market_obs["load_actual"],
            market_obs["load_forecast_error"],
            market_obs["renewable_pct"],
            market_obs["temperature_anomaly"],
            market_obs["inter_province_flow"],
            market_obs["unit_outage_capacity"],
            # D. Forecast distribution (8)
            forecast["price_mean_4h"],
            forecast["price_p90_4h"],
            forecast["price_p10_4h"],
            forecast["load_mean_4h"],
            forecast["load_uncertainty_4h"],
            forecast["renewable_mean_4h"],
            forecast["renewable_uncertainty_4h"],
            forecast["weather_anomaly"],
            # E. 2nd-order interactions (3)
            market_obs["temperature_anomaly"] * (1 - market_obs["renewable_pct"]),
            market_obs["load_forecast_error"] * market_obs["spot_price_volatility"],
            cumulative["deviation_pct"] * time_info["days_to_month_end"],
        ],
        dtype=float,
    )
