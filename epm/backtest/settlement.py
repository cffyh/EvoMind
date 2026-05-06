"""偏差考核 + 收益结算 — provincial-rules-driven, ported from src_legacy/backtest_gd.py.

Single-period settlement (one (sale_market, target_day, period) row).
The four cases in `dayahead_bid_income` mirror the original `BackTest`
class but parameterized on `MarketRules` so a different province with
different λ₀ / μ / penalty multiplier drops in cleanly.
"""
from __future__ import annotations

from dataclasses import dataclass

from epm.config import MarketRules


@dataclass(frozen=True)
class SettlementResult:
    profit: float
    income_gross: float          # before deviation penalty
    deviation_cost: float
    load_diff: float             # positive = the over/under-shoot magnitude


def settle_period(
    rules: MarketRules,
    *,
    da_price: float,
    rt_price: float,
    declared_q: float,
    realized_load: float,
) -> SettlementResult:
    """Apply the case-1/case-2 偏差考核 from v2.0 §4.1.2 + 广东 spec.

    Reference: `src_legacy/backtest_gd.py`. Logic preserved verbatim;
    the only change is parameterizing λ₀ / μ via `rules`, and folding
    the optional `penalty_multiplier` into μ so per-province 2×罚款 etc.
    drops in.
    """
    lam, mu = rules.lambda_0, rules.mu * rules.penalty_multiplier
    upper = realized_load * (1 + lam)
    lower = realized_load * (1 - lam)

    if declared_q > upper and da_price < rt_price:
        load_diff = declared_q - upper
        deviation_cost = load_diff * (rt_price - da_price) * mu
    elif declared_q < lower and da_price > rt_price:
        load_diff = lower - declared_q
        deviation_cost = load_diff * (da_price - rt_price) * mu
    else:
        load_diff = 0.0
        deviation_cost = 0.0

    income_gross = (rt_price - da_price) * (declared_q - realized_load)
    profit = income_gross - deviation_cost
    return SettlementResult(
        profit=round(profit, 3),
        income_gross=round(income_gross, 3),
        deviation_cost=round(deviation_cost, 3),
        load_diff=load_diff,
    )
