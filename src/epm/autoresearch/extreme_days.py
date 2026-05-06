"""极端日子集 — v2.0 §6.4.

Each evaluation report MUST break out performance on these subsets, not
just the integrated mean. A strategy that improves the mean while
crashing on cold-snap days is unacceptable.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ExtremeDayLabels:
    high_temp: pd.Series   # bool series indexed by target_day
    cold_snap: pd.Series
    holiday: pd.Series
    high_renewable: pd.Series
    peak_load: pd.Series
    policy_anomaly: pd.Series

    def any_extreme(self) -> pd.Series:
        return self.high_temp | self.cold_snap | self.holiday | self.high_renewable | self.peak_load | self.policy_anomaly


def classify_extreme_days(
    daily: pd.DataFrame,
    *,
    holiday_dates: set[str] | None = None,
    policy_anomaly_dates: set[str] | None = None,
) -> ExtremeDayLabels:
    """Tag each day in `daily` with extreme labels.

    Expected columns on `daily` (one row per day):
      - target_day, max_temperature, min_temperature, max_load, renewable_pct
    Holiday + policy-anomaly dates come from external calendars / monitoring.
    """
    holiday_dates = holiday_dates or set()
    policy_anomaly_dates = policy_anomaly_dates or set()

    df = daily.copy()
    df.index = df["target_day"]

    high_temp = df["max_temperature"] > df["max_temperature"].quantile(0.95)
    cold_snap = df["min_temperature"] < df["min_temperature"].quantile(0.05)
    high_renew = df["renewable_pct"] > df["renewable_pct"].quantile(0.90)
    peak_load = df["max_load"] > df["max_load"].quantile(0.90)

    holiday = df["target_day"].isin(holiday_dates)
    policy = df["target_day"].isin(policy_anomaly_dates)
    holiday.index = df["target_day"]
    policy.index = df["target_day"]

    return ExtremeDayLabels(
        high_temp=high_temp,
        cold_snap=cold_snap,
        holiday=holiday,
        high_renewable=high_renew,
        peak_load=peak_load,
        policy_anomaly=policy,
    )
