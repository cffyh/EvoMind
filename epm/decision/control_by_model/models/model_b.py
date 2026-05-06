"""Model B — 高波动日 / DRO.

Distributionally Robust Optimization: 扩大不确定性集合，把更多预算
留到实时市场再决策。比 Model A 更保守，CVaR 约束更紧。
"""
from __future__ import annotations

from dataclasses import dataclass

from epm.decision.stochastic_program import SPInputs

from .base import ModelOutput


@dataclass
class ModelB:
    name: str = "B"
    ambiguity_radius: float = 0.10   # Wasserstein / phi-divergence 半径
    realtime_budget_share: float = 0.40
    cvar_alpha: float = 0.97

    def decide(self, inputs: SPInputs) -> ModelOutput:  # pragma: no cover — TODO M5
        raise NotImplementedError("Model B / DRO — see v2.0 §4.4.3")
