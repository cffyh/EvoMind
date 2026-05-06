"""回测引擎质量硬指标 — v2.0 §6.7.

不达标则禁止启动 RL 训练。Run on a frozen historical 人工策略 baseline:
the simulator's outputs must match real settlement to within these
tolerances, otherwise the FQI training is learning a fictional environment.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


# 阈值来自 v2.0 §6.7.1
COST_DEVIATION_TOL = 0.02      # 总成本相对差距 < 2%
DEVIATION_RATE_ABS_TOL = 0.005  # 偏差率绝对差 < 0.5pp
PERIOD_MAPE_TOL = 0.05         # 时段级 MAPE < 5%


@dataclass
class FidelityReport:
    cost_deviation_rel: float
    deviation_rate_abs_diff: float
    period_mape: float
    passed: bool
    failures: list[str]


def fidelity_check(simulated: pd.DataFrame, realized: pd.DataFrame) -> FidelityReport:
    """Compare simulator output (`simulated`) against true settlement (`realized`).

    Both frames must share columns ['target_day', 'period', 'cost'] and align row-wise
    after sorting on (target_day, period).
    """
    s = simulated.sort_values(["target_day", "period"]).reset_index(drop=True)
    r = realized.sort_values(["target_day", "period"]).reset_index(drop=True)
    if len(s) != len(r):
        raise ValueError(f"length mismatch: sim={len(s)} real={len(r)}")

    sim_total = float(s["cost"].sum())
    real_total = float(r["cost"].sum())
    cost_dev = abs(sim_total - real_total) / max(abs(real_total), 1e-9)

    sim_dev = float(s["deviation_rate"].mean()) if "deviation_rate" in s else 0.0
    real_dev = float(r["deviation_rate"].mean()) if "deviation_rate" in r else 0.0
    dev_diff = abs(sim_dev - real_dev)

    nonzero = r["cost"].abs() > 1e-6
    if nonzero.sum() == 0:
        period_mape = 0.0
    else:
        period_mape = float(np.mean(np.abs(s.loc[nonzero, "cost"] - r.loc[nonzero, "cost"]) / r.loc[nonzero, "cost"].abs()))

    failures: list[str] = []
    if cost_dev >= COST_DEVIATION_TOL:
        failures.append(f"cost_deviation_rel={cost_dev:.4f} >= {COST_DEVIATION_TOL}")
    if dev_diff >= DEVIATION_RATE_ABS_TOL:
        failures.append(f"deviation_rate_abs_diff={dev_diff:.4f} >= {DEVIATION_RATE_ABS_TOL}")
    if period_mape >= PERIOD_MAPE_TOL:
        failures.append(f"period_mape={period_mape:.4f} >= {PERIOD_MAPE_TOL}")

    return FidelityReport(
        cost_deviation_rel=cost_dev,
        deviation_rate_abs_diff=dev_diff,
        period_mape=period_mape,
        passed=not failures,
        failures=failures,
    )
