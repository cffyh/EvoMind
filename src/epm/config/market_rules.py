"""省份市场规则参数化 — v2.0 §5.4.

Each province plugs in its own MarketRules; downstream code (settlement,
risk_guard, compliance) consumes only this object. Adding a new province
means adding a new MarketRules instance, not editing logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MarketRules:
    """Province-specific market parameters.

    Fields mirror the differences enumerated in v2.0 §5.4 (跨省结算规则差异):
    deviation thresholds, penalty multipliers, declaration price bounds,
    declaration cadence, settlement model, and information-availability lags.
    """

    name: str

    # 偏差考核 — settlement.py uses these
    lambda_0: float           # 偏差带阈值 (e.g. 0.20 = ±20%)
    mu: float                 # 收益回收系数 (惩罚倍数, e.g. 1.0 / 2.0)
    penalty_multiplier: float # 部分省份超阈值后再乘倍数 (e.g. 2.0 for 2 倍罚款)

    # 申报机制
    declaration_mode: str     # "quantity_only" | "quantity_price" | "multi_segment"
    n_periods_per_day: int    # 24 (hourly) or 96 (15-min)
    period_minutes: int       # 60 or 15

    # 价格上下限 (元/MWh)
    price_floor: float
    price_cap: float
    allow_negative_price: bool

    # 信息时效 (天) — feature_store / static_scanner enforce these
    settle_price_delay_days: int      # 结算价 D-N
    realtime_node_price_delay_days: int  # 实时出清价 D-N
    dayahead_node_price_delay_days: int  # 日前出清价 D-N
    actual_load_delay_days: int       # 实际负荷 D-N
    forecast_available_days: int      # 预测信息 D-N

    # 中长期合约配比 (v2.0 §5.3.2 区间)
    lt_ratio_default: float = 0.80
    lt_ratio_high_vol: float = 0.875  # 夏冬尖峰
    lt_ratio_mid_vol: float = 0.80    # 过渡期
    lt_ratio_low_vol: float = 0.725   # 平稳期

    # 风控硬约束默认值 — risk_guard 读取
    cvar_alpha: float = 0.95
    daily_spend_cap_yuan: float = field(default=float("inf"))
    period_position_cap_mwh: float = field(default=float("inf"))


# 广东 (basis for the current AutoResearch loop) — 数据为小时级.
GUANGDONG = MarketRules(
    name="GD",
    lambda_0=0.20,
    mu=1.0,
    penalty_multiplier=1.0,
    declaration_mode="quantity_only",
    n_periods_per_day=24,
    period_minutes=60,
    price_floor=0.0,
    price_cap=1500.0,
    allow_negative_price=False,
    settle_price_delay_days=7,
    realtime_node_price_delay_days=4,
    dayahead_node_price_delay_days=1,
    actual_load_delay_days=6,
    forecast_available_days=1,
)


REGISTRY: dict[str, MarketRules] = {
    GUANGDONG.name: GUANGDONG,
}


def get(name: str) -> MarketRules:
    if name not in REGISTRY:
        raise KeyError(f"unknown province: {name!r}; registered: {list(REGISTRY)}")
    return REGISTRY[name]
