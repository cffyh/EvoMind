"""Model C — 极端日 (高温/寒潮/重大节假日).

全保守：直接按偏差带上限申报，最大化避险。This is a closed form,
no SP solving required.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from epm.decision.stochastic_program import SPInputs

from .base import ModelOutput


@dataclass
class ModelC:
    name: str = "C"

    def decide(self, inputs: SPInputs) -> ModelOutput:
        rules = inputs.rules
        T = rules.n_periods_per_day

        # Average forecast load across scenarios — the most defensible
        # central tendency under uncertainty.
        if not inputs.scenarios:
            raise ValueError("Model C needs at least one scenario for L̂")
        loads = np.stack([s.load for s in inputs.scenarios])
        load_central = loads.mean(axis=0)

        # Conservative declaration: stay strictly inside the deviation band.
        q_da = load_central - inputs.lt_quota  # net spot procurement
        # Clip the spot quantity to the (1 ± λ₀) band defined against load_central.
        upper = load_central * (1 + rules.lambda_0) - inputs.lt_quota
        lower = load_central * (1 - rules.lambda_0) - inputs.lt_quota
        q_da = np.clip(q_da, lower, upper)

        return ModelOutput(
            q_da=q_da,
            diagnostics={"strategy": "extreme-day-conservative", "load_central": load_central.tolist()},
        )
