"""外层模型选择器 — v2.0 §4.4.3.

Agent 不直接出价，而是选「今天用 A/B/C/D/E 中哪个报价骨架 +
哪组参数」。AutoResearch 可以迭代特征工程与选择器结构，
**但不能新增/删除模型库条目** —— 模型库由人工设计并冻结。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class ModelChoice(str, Enum):
    A_NORMAL = "A"      # 低波动正常日 — 标准两阶段 SP
    B_HIGH_VOL = "B"    # 高波动日 — DRO + 更多预算留实时
    C_EXTREME = "C"     # 极端日 — 全保守按偏差带上限申报
    D_POLICY = "D"      # 政策异动 / 规则变更 — Agent 仅出建议
    E_LOW_PRICE = "E"   # 低价机会日 — 预算前置


@dataclass
class SelectorState:
    """Inputs the selector reads. Keep this stable — feature engineering
    happens upstream in `epm/data/feature_store.py`.
    """
    realized_vol_recent: float        # 前 N 日已实现波动率
    forecast_vol_today: float         # 当日预测波动率
    is_extreme_day: bool              # 极端日标志（高温/寒潮/重大节假日）
    is_policy_anomaly: bool           # 政策异动日（监管文件订阅触发）
    forecast_negprice_prob: float     # 当日出现负电价的预测概率
    cvar_param_ci_width: float        # SV 参数估计置信区间宽度（过宽触发 D）


def select_model(state: SelectorState, *, vol_high: float = 80.0, vol_low: float = 25.0) -> ModelChoice:
    """Rule-based selector. AutoResearch may replace this with a learned
    classifier, but the output type must stay `ModelChoice`.
    """
    if state.is_policy_anomaly or state.cvar_param_ci_width > 0.5:
        return ModelChoice.D_POLICY
    if state.is_extreme_day:
        return ModelChoice.C_EXTREME
    if state.forecast_vol_today >= vol_high or state.realized_vol_recent >= vol_high:
        return ModelChoice.B_HIGH_VOL
    if state.forecast_negprice_prob > 0.20 and state.forecast_vol_today <= vol_low:
        return ModelChoice.E_LOW_PRICE
    return ModelChoice.A_NORMAL


_DESCRIPTIONS: Mapping[ModelChoice, str] = {
    ModelChoice.A_NORMAL: "两阶段 SP，场景数 200，CVaR 适中",
    ModelChoice.B_HIGH_VOL: "DRO，扩大不确定性集合，更多预算留到实时",
    ModelChoice.C_EXTREME: "全保守，按偏差带上限申报，最大化避险",
    ModelChoice.D_POLICY: "强制人工介入，Agent 仅给出建议",
    ModelChoice.E_LOW_PRICE: "预算前置，加大日前比例减少实时敞口",
}


def describe(choice: ModelChoice) -> str:
    return _DESCRIPTIONS[choice]
