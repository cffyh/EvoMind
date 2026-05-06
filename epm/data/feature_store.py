"""Feature engineering — strict no-future-leakage by construction.

The single rule across the whole package: every historical aggregate must
go through `.shift(rules.<delay>)` BEFORE `.rolling(...)`. The shift amount
is read from the active `MarketRules`, not hard-coded, so per-province lag
differences (v2.0 §5.4) never leak into a feature pipeline written for
another province.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from epm.config import MarketRules


def build_rolling_features(
    df: pd.DataFrame,
    rules: MarketRules,
    *,
    node_window: int = 7,
    settle_window: int = 10,
    load_window: int = 7,
) -> pd.DataFrame:
    """Per-period rolling stats lagged by `rules.*_delay_days` shifts.

    Mirrors what `strategy.py` builds today, but parameterized on `rules` so
    a province with different settlement-price lag drops in cleanly.
    """
    df = df.copy()

    df["forecast_load"] = df.get("forecast_total_load_info")
    df["forecast_a_power"] = df.get("forecast_province_a_power")
    df["forecast_b_power"] = df.get("forecast_province_b_power")
    df["forecast_local"] = df.get("forecast_local_power_output")
    df["overhaul_total"] = df.get("forecast_overhaul_total_capacity")
    df["overhaul_market"] = df.get("forecast_overhaul_market_capacity")
    df["hour"] = df["period"]
    df["da_node_price"] = df["da_node"]

    settle_shift = rules.settle_price_delay_days
    node_shift = rules.realtime_node_price_delay_days
    load_shift = rules.actual_load_delay_days

    parts = []
    for period in range(rules.n_periods_per_day):
        pdf = df[df["period"] == period].copy().sort_values("target_day").reset_index(drop=True)
        if pdf.empty:
            continue

        dart_s = pdf["dart_settle"]
        pdf["settle_dart_mean"] = dart_s.shift(settle_shift).rolling(settle_window, min_periods=1).mean()
        pdf["settle_dart_std"] = dart_s.shift(settle_shift).rolling(settle_window, min_periods=2).std()
        pdf["settle_dart_pos_rate"] = (
            dart_s.shift(settle_shift).rolling(settle_window, min_periods=1).apply(lambda x: (x > 0).mean())
        )

        dart_n = pdf["dart_node"]
        pdf["node_dart_mean"] = dart_n.shift(node_shift).rolling(node_window, min_periods=1).mean()
        pdf["node_dart_std"] = dart_n.shift(node_shift).rolling(node_window, min_periods=2).std()
        pdf["node_dart_pos_rate"] = (
            dart_n.shift(node_shift).rolling(node_window, min_periods=1).apply(lambda x: (x > 0).mean())
        )

        pdf["hist_load_mean"] = pdf["load"].shift(load_shift).rolling(load_window, min_periods=1).mean()

        rt_node_mean = pdf["rt_node"].shift(node_shift).rolling(node_window, min_periods=1).mean()
        pdf["da_vs_recent_rt"] = pdf["da_node"] - rt_node_mean

        parts.append(pdf)

    out = pd.concat(parts, ignore_index=True).sort_values(["target_day", "period"]).reset_index(drop=True)
    out["node_dart_snr"] = out["node_dart_mean"] / out["node_dart_std"].replace(0, np.nan)
    out["settle_dart_snr"] = out["settle_dart_mean"] / out["settle_dart_std"].replace(0, np.nan)
    out["da_node_x_pos_rate"] = out["da_node_price"] * out["node_dart_pos_rate"]
    return out
