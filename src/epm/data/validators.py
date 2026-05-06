"""Data quality + leakage runtime checks.

These are runtime asserts (the static-source check lives in
`autoresearch/static_scanner.py`). Call them at the boundary of every
feature pipeline.
"""
from __future__ import annotations

import pandas as pd

from epm.config import MarketRules


def assert_no_future_leakage(features: pd.DataFrame, decision_day: str, rules: MarketRules) -> None:
    """Verify that no feature row references information past `decision_day`.

    Only structural checks — does not catch a numeric value that came from
    the future via a missing .shift(). Pair with static_scanner.py.
    """
    cutoff = pd.Timestamp(decision_day)

    if "target_day" not in features.columns:
        raise ValueError("features missing 'target_day' column")

    if pd.to_datetime(features["target_day"]).max() > cutoff + pd.Timedelta(days=rules.forecast_available_days):
        raise ValueError(
            f"feature frame contains rows past decision_day={decision_day} "
            f"+ forecast_available_days={rules.forecast_available_days}"
        )


def summary_check(df: pd.DataFrame, *, expected_periods_per_day: int) -> dict:
    """Quick coverage summary — periods per day, NaN counts, date span."""
    by_day = df.groupby("target_day").size()
    return {
        "n_rows": len(df),
        "n_days": by_day.size,
        "first_day": str(by_day.index.min()) if not by_day.empty else None,
        "last_day": str(by_day.index.max()) if not by_day.empty else None,
        "incomplete_days": [(d, int(c)) for d, c in by_day.items() if int(c) != expected_periods_per_day],
        "nan_counts": df.isna().sum().to_dict(),
    }
