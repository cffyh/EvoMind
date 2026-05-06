"""回测引擎 — v2.0 §6.7 / §8.2.

Hard requirements:
- 严格 T+1 模拟 (declaration → clearing → realtime → settlement)
- 规则可配置（按 `MarketRules` 参数化）
- 避免自回测谬误（默认假设我方报价对市场无影响；大额时告警）
- 多版本对比（同一时段段可同时跑多套策略）
- 可视化复盘到时段级别

The engine consumes a strategy callable
    fn(actual_frame: DataFrame) -> DataFrame[strategy_declary_load]
and produces both daily and per-period profit frames + summary metrics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from epm.config import MarketRules

from .settlement import settle_period


StrategyFn = Callable[[pd.DataFrame], pd.DataFrame]


@dataclass
class BacktestRun:
    by_period: pd.DataFrame  # row-per-period: profit, deviation_cost, load_diff
    by_day: pd.DataFrame     # row-per-day: total profit, total optimal, ratio
    summary: dict            # cost_mean, cvar, deviation_rate, achievement_ratio


@dataclass
class BacktestEngine:
    rules: MarketRules

    def run(
        self,
        actual: pd.DataFrame,
        strategy: StrategyFn,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> BacktestRun:
        """Walk through `actual` chronologically, settle each period, aggregate."""
        df_strategy = strategy(actual)

        merged = actual.merge(
            df_strategy[["sale_market", "target_day", "period", "strategy_declary_load"]],
            on=["sale_market", "target_day", "period"],
            how="inner",
        )
        if start_date:
            merged = merged[merged["target_day"] >= start_date]
        if end_date:
            merged = merged[merged["target_day"] <= end_date]
        merged = merged.sort_values(["target_day", "period"]).reset_index(drop=True)

        rows = []
        optimal_rows = []
        for _, r in merged.iterrows():
            res = settle_period(
                self.rules,
                da_price=r["actual_day_ahead_price"],
                rt_price=r["actual_realtime_price"],
                declared_q=r["strategy_declary_load"],
                realized_load=r["actual_realtime_load"],
            )
            rows.append(
                {
                    **r.to_dict(),
                    "profit": res.profit,
                    "deviation_cost": res.deviation_cost,
                    "load_diff": res.load_diff,
                }
            )
            best_q = (
                r["actual_realtime_load"] * (1 - self.rules.lambda_0)
                if r["actual_day_ahead_price"] >= r["actual_realtime_price"]
                else r["actual_realtime_load"] * (1 + self.rules.lambda_0)
            )
            best = settle_period(
                self.rules,
                da_price=r["actual_day_ahead_price"],
                rt_price=r["actual_realtime_price"],
                declared_q=best_q,
                realized_load=r["actual_realtime_load"],
            )
            optimal_rows.append(best.profit)

        by_period = pd.DataFrame(rows)
        by_period["best_profit"] = optimal_rows

        by_day = (
            by_period.groupby(["sale_market", "target_day"], as_index=False)
            .agg(strategy_profit=("profit", "sum"), best_profit=("best_profit", "sum"))
        )
        total_strategy = float(by_day["strategy_profit"].sum())
        total_best = float(by_day["best_profit"].sum())
        achievement_ratio = total_strategy / total_best if total_best != 0 else 0.0

        deviation_rate = float(by_period["load_diff"].abs().sum() / by_period["actual_realtime_load"].sum())
        cost_mean = -float(by_period["profit"].mean())  # cost = -profit, buyer-side framing
        losses = -by_period["profit"].to_numpy()
        from epm.risk.var_cvar import conditional_value_at_risk
        cvar = conditional_value_at_risk(losses, alpha=self.rules.cvar_alpha)

        summary = {
            "achievement_ratio": achievement_ratio,
            "total_strategy_profit": total_strategy,
            "total_best_profit": total_best,
            "cost_mean": cost_mean,
            "cvar": cvar,
            "deviation_rate": deviation_rate,
            "n_periods": len(by_period),
        }
        return BacktestRun(by_period=by_period, by_day=by_day, summary=summary)
