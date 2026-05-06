"""Model E — 低价机会日.

预算前置策略：加大日前比例减少实时敞口。Used when forecast volatility
is low AND there's a meaningful negative-price probability.
"""
from __future__ import annotations

from dataclasses import dataclass

from epm.decision.stochastic_program import SPInputs

from .base import ModelOutput


@dataclass
class ModelE:
    name: str = "E"
    realtime_budget_share: float = 0.10  # 留 10% 给实时；正常日 20–25%

    def decide(self, inputs: SPInputs) -> ModelOutput:  # pragma: no cover — TODO M5
        raise NotImplementedError("Model E — see v2.0 §4.4.3")
