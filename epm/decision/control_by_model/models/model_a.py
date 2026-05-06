"""Model A — 低波动正常日.

两阶段 SP，场景数 200，CVaR 阈值适中。This is the workhorse — used by
default when nothing weird is happening.
"""
from __future__ import annotations

from dataclasses import dataclass

from epm.decision.stochastic_program import SPInputs, solve as solve_sp

from .base import ModelOutput


@dataclass
class ModelA:
    name: str = "A"
    n_scenarios: int = 200
    cvar_alpha: float = 0.95
    smoothness_delta: float = 0.10  # ±10% 相邻时段平滑

    def decide(self, inputs: SPInputs) -> ModelOutput:
        sol = solve_sp(inputs)  # raises NotImplementedError until solver wired
        return ModelOutput(q_da=sol.q_da, p_da=sol.p_da, diagnostics={"objective": sol.objective})
