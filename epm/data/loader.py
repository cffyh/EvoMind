"""数据中台 — 原始数据层.

Reads the raw Excel files in `data/`, normalizes column names and joins
hourly + 15-min sources to a single per-(market, day, period) frame.
The shape mirrors what `strategy.py` already does, lifted out so all
modules share one canonical loader.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

from epm.config import SETTINGS

HOURLY_FILE = "GD_power_spot_hourly_data.xlsx"
QUARTER_FILE = "GD_power_spot_15min_data.xlsx"


def _data_path(name: str) -> str:
    return os.path.join(SETTINGS.data_dir, name)


def load_hourly(path: str | None = None) -> pd.DataFrame:
    """Load the hourly Excel into a flat frame with normalized period column."""
    df = pd.read_excel(path or _data_path(HOURLY_FILE))
    df["target_day"] = pd.to_datetime(df["target_day"]).dt.strftime("%Y-%m-%d")
    df["period"] = pd.to_datetime(df["time_period_name"], errors="coerce").dt.hour
    return df


def load_15min(path: str | None = None) -> pd.DataFrame:
    """Load the 15-min Excel and aggregate to hourly granularity."""
    df = pd.read_excel(path or _data_path(QUARTER_FILE))
    df["target_day"] = pd.to_datetime(df["target_day"]).dt.strftime("%Y-%m-%d")
    df["period"] = pd.to_datetime(df["time_period_name"], errors="coerce").dt.hour
    agg_cols = {
        "forecast_total_load_info": "mean",
        "forecast_province_a_power": "mean",
        "forecast_province_b_power": "mean",
        "forecast_local_power_output": "mean",
        "forecast_overhaul_total_capacity": "mean",
        "forecast_overhaul_market_capacity": "mean",
        "actual_total_load_info": "mean",
        "actual_province_b_power": "mean",
        "actual_west_to_east_power": "mean",
    }
    keep = [c for c in agg_cols if c in df.columns]
    return df.groupby(["sale_market", "target_day", "period"]).agg({c: agg_cols[c] for c in keep}).reset_index()


def _parse_json_mean(value: object) -> float:
    """Hourly weather columns store per-city JSON; collapse to a province mean."""
    try:
        data = json.loads(value) if isinstance(value, str) else value
        vals = [float(list(d.values())[0]) for d in data]
        return float(np.mean(vals))
    except Exception:
        return float("nan")


def load_and_merge() -> pd.DataFrame:
    """Join hourly + 15-min, derive DART labels and weather scalars."""
    df_h = load_hourly()
    df_q = load_15min()

    df = pd.merge(df_h, df_q, on=["sale_market", "target_day", "period"], how="left")

    df["da_settle"] = df["actual_day_ahead_settle_elec_price"]
    df["rt_settle"] = df["actual_realtime_settle_elec_price"]
    df["da_node"] = df["actual_day_ahead_node_elec_price"]
    df["rt_node"] = df["actual_realtime_node_elec_price"]
    df["load"] = df["actual_total_load"]
    df["dart_settle"] = df["da_settle"] - df["rt_settle"]
    df["dart_node"] = df["da_node"] - df["rt_node"]

    dt = pd.to_datetime(df["target_day"])
    df["weekday"] = dt.dt.weekday
    df["month"] = dt.dt.month
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)
    df["day_idx"] = (dt - dt.min()).dt.days

    if "temperature" in df.columns:
        df["avg_temperature"] = df["temperature"].apply(_parse_json_mean)
    if "dswrf" in df.columns:
        df["avg_irradiance"] = df["dswrf"].apply(_parse_json_mean)

    return df.sort_values(["target_day", "period"]).reset_index(drop=True)
