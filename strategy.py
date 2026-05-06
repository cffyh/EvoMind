"""
交易策略 v4.0 — XGBoost 超参优化 + 时间衰减权重
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

LAMBDA_0 = 0.2
TRAIN_WINDOW_DAYS = 180
RETRAIN_INTERVAL = 7
SETTLE_DELAY = 7
NODE_RT_DELAY = 4
LOAD_DELAY = 6

FEATURE_COLS = [
    "hour", "weekday", "month", "is_weekend",
    "forecast_load", "forecast_a_power", "forecast_b_power",
    "forecast_local", "overhaul_total", "overhaul_market",
    "supply_demand_ratio", "overhaul_ratio",
    "da_node_price",
    "settle_dart_mean", "settle_dart_std", "settle_dart_pos_rate",
    "node_dart_mean", "node_dart_std", "node_dart_pos_rate",
    "hist_load_mean", "da_vs_recent_rt",
    "avg_temperature", "avg_irradiance",
    "da_node_x_pos_rate",
    "node_dart_snr",
    "settle_dart_snr",
]


def load_and_merge_data() -> pd.DataFrame:
    """加载并合并所有数据源"""
    df_h = pd.read_excel(os.path.join(DATA_DIR, "GD_power_spot_hourly_data.xlsx"))
    df_h["target_day"] = pd.to_datetime(df_h["target_day"]).dt.strftime("%Y-%m-%d")
    df_h["period"] = pd.to_datetime(df_h["time_period_name"], errors="coerce").dt.hour

    df_15 = pd.read_excel(os.path.join(DATA_DIR, "GD_power_spot_15min_data.xlsx"))
    df_15["target_day"] = pd.to_datetime(df_15["target_day"]).dt.strftime("%Y-%m-%d")
    df_15["period"] = pd.to_datetime(df_15["time_period_name"], errors="coerce").dt.hour
    df_15h = df_15.groupby(["sale_market", "target_day", "period"]).agg({
        "forecast_total_load_info": "mean",
        "forecast_province_a_power": "mean",
        "forecast_province_b_power": "mean",
        "forecast_local_power_output": "mean",
        "forecast_overhaul_total_capacity": "mean",
        "forecast_overhaul_market_capacity": "mean",
        "actual_total_load_info": "mean",
        "actual_province_b_power": "mean",
        "actual_west_to_east_power": "mean",
    }).reset_index()

    df = pd.merge(df_h, df_15h, on=["sale_market", "target_day", "period"], how="left")

    df["da_settle"] = df["actual_day_ahead_settle_elec_price"]
    df["rt_settle"] = df["actual_realtime_settle_elec_price"]
    df["da_node"] = df["actual_day_ahead_node_elec_price"]
    df["rt_node"] = df["actual_realtime_node_elec_price"]
    df["load"] = df["actual_total_load"]
    df["dart_settle"] = df["da_settle"] - df["rt_settle"]
    df["dart_node"] = df["da_node"] - df["rt_node"]
    df["label"] = (df["dart_settle"] > 0).astype(int)

    dt = pd.to_datetime(df["target_day"])
    df["weekday"] = dt.dt.weekday
    df["month"] = dt.dt.month
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)
    df["day_idx"] = (dt - dt.min()).dt.days

    total_supply = (df["forecast_province_a_power"].fillna(0) +
                    df["forecast_province_b_power"].fillna(0) +
                    df["forecast_local_power_output"].fillna(0))
    df["supply_demand_ratio"] = np.where(total_supply > 0, df["forecast_total_load_info"] / total_supply, np.nan)
    df["overhaul_ratio"] = np.where(total_supply > 0, df["forecast_overhaul_market_capacity"].fillna(0) / total_supply, np.nan)

    def parse_json_mean(s):
        try:
            data = json.loads(s) if isinstance(s, str) else s
            vals = [float(list(d.values())[0]) for d in data]
            return np.mean(vals)
        except:
            return np.nan

    df["avg_temperature"] = df["temperature"].apply(parse_json_mean)
    df["avg_irradiance"] = df["dswrf"].apply(parse_json_mean)

    return df.sort_values(["target_day", "period"]).reset_index(drop=True)


def build_rolling_features(df: pd.DataFrame, node_window=11, settle_window=7) -> pd.DataFrame:
    """按 period 分组计算历史滚动统计量"""
    df = df.copy()

    df["forecast_load"] = df["forecast_total_load_info"]
    df["forecast_a_power"] = df["forecast_province_a_power"]
    df["forecast_b_power"] = df["forecast_province_b_power"]
    df["forecast_local"] = df["forecast_local_power_output"]
    df["overhaul_total"] = df["forecast_overhaul_total_capacity"]
    df["overhaul_market"] = df["forecast_overhaul_market_capacity"]
    df["hour"] = df["period"]
    df["da_node_price"] = df["da_node"]

    settle_shift = SETTLE_DELAY
    node_shift = NODE_RT_DELAY

    features_list = []

    for period in range(24):
        pdf = df[df["period"] == period].copy().sort_values("target_day").reset_index(drop=True)

        dart_s = pdf["dart_settle"]
        pdf["settle_dart_mean"] = dart_s.shift(settle_shift).rolling(settle_window, min_periods=1).mean()
        pdf["settle_dart_std"] = dart_s.shift(settle_shift).rolling(settle_window, min_periods=2).std()
        pdf["settle_dart_pos_rate"] = dart_s.shift(settle_shift).rolling(settle_window, min_periods=1).apply(lambda x: (x > 0).mean())

        dart_n = pdf["dart_node"]
        pdf["node_dart_mean"] = dart_n.shift(node_shift).rolling(node_window, min_periods=1).mean()
        pdf["node_dart_std"] = dart_n.shift(node_shift).rolling(node_window, min_periods=2).std()
        pdf["node_dart_pos_rate"] = dart_n.shift(node_shift).rolling(node_window, min_periods=1).apply(lambda x: (x > 0).mean())
        pdf["hist_load_mean"] = pdf["load"].shift(LOAD_DELAY).rolling(7, min_periods=1).mean()

        rt_node_mean = pdf["rt_node"].shift(node_shift).rolling(node_window, min_periods=1).mean()
        pdf["da_vs_recent_rt"] = pdf["da_node"] - rt_node_mean

        features_list.append(pdf)

    df_feat = pd.concat(features_list, ignore_index=True)
    df_feat = df_feat.sort_values(["target_day", "period"]).reset_index(drop=True)
    df_feat["da_node_x_pos_rate"] = df_feat["da_node_price"] * df_feat["node_dart_pos_rate"]
    df_feat["node_dart_snr"] = df_feat["node_dart_mean"] / df_feat["node_dart_std"].replace(0, np.nan)
    df_feat["settle_dart_snr"] = df_feat["settle_dart_mean"] / df_feat["settle_dart_std"].replace(0, np.nan)
    return df_feat


def run_strategy(start_date: str, end_date: str) -> pd.DataFrame:
    """XGBoost 滚动训练 + 时间衰减权重 + 混合投票"""
    df = load_and_merge_data()
    df = build_rolling_features(df, node_window=7, settle_window=10)

    dates = sorted(df["target_day"].unique())
    target_dates = [d for d in dates if start_date <= d <= end_date]

    model = None
    last_train_date = None
    results = []

    for target_day in target_dates:
        target_dt = datetime.strptime(target_day, "%Y-%m-%d")

        need_retrain = (
            model is None or
            last_train_date is None or
            (target_dt - last_train_date).days >= RETRAIN_INTERVAL
        )

        if need_retrain:
            label_end = (target_dt - timedelta(days=SETTLE_DELAY)).strftime("%Y-%m-%d")
            label_start = (target_dt - timedelta(days=SETTLE_DELAY + TRAIN_WINDOW_DAYS)).strftime("%Y-%m-%d")

            train_mask = (df["target_day"] >= label_start) & (df["target_day"] <= label_end)
            train_df = df[train_mask]

            if len(train_df) >= 240:
                X_train = train_df[FEATURE_COLS].copy()
                y_train = train_df["label"].values

                train_days = (pd.to_datetime(train_df["target_day"]) -
                              pd.to_datetime(label_start)).dt.days.values
                max_days = train_days.max()
                sample_weights = np.exp(-0.005 * (max_days - train_days))

                model = XGBClassifier(
                    n_estimators=180,
                    max_depth=3,
                    learning_rate=0.08,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_alpha=1.0,
                    reg_lambda=2.0,
                    gamma=0.02,
                    min_child_weight=8,
                    eval_metric="logloss",
                    verbosity=0,
                    random_state=42,
                )
                model.fit(X_train, y_train, sample_weight=sample_weights)
                last_train_date = target_dt
            else:
                model = None

        day_df = df[df["target_day"] == target_day]
        for _, row in day_df.iterrows():
            actual_load = row["load"]
            sale_market = row["sale_market"]
            period = row["period"]

            if model is not None:
                X_pred = pd.DataFrame([row[FEATURE_COLS]])
                prob_positive = model.predict_proba(X_pred)[0, 1]
            else:
                prob_positive = 0.5

            xgb_signal = 1 if prob_positive > 0.5 else -1

            pos_rate = row.get("node_dart_pos_rate", 0.5)
            pos_rate = pos_rate if not np.isnan(pos_rate) else 0.5
            rule_signal = 1 if pos_rate > 0.57 else -1

            if prob_positive > 0.75 or prob_positive < 0.25:
                final_signal = xgb_signal
            elif xgb_signal == rule_signal:
                final_signal = xgb_signal
            else:
                final_signal = rule_signal

            if final_signal > 0:
                declare_load = actual_load * (1 - LAMBDA_0)
            else:
                declare_load = actual_load * (1 + LAMBDA_0)

            declare_load = max(declare_load, 0.01)
            results.append({
                "sale_market": sale_market,
                "target_day": target_day,
                "period": int(period),
                "strategy_declary_load": declare_load,
            })

    return pd.DataFrame(results).sort_values(["sale_market", "target_day", "period"]).reset_index(drop=True)
