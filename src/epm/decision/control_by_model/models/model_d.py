"""Model D — 政策异动日 / 市场规则变更日.

强制人工介入：Agent 仅给出建议（来自 Model A），并把 `requires_human_review`
置 True。最终申报必须由交易员审核。
"""
from __future__ import annotations

from dataclasses import dataclass

from epm.decision.stochastic_program import SPInputs

from .base import ModelOutput
from .model_a import ModelA


@dataclass
class ModelD:
    name: str = "D"

    def decide(self, inputs: SPInputs) -> ModelOutput:
        try:
            advisory = ModelA().decide(inputs)
        except NotImplementedError:
            # Even when SP solver isn't ready, Model D should never auto-execute.
            advisory = ModelOutput(q_da=inputs.lt_quota * 0)
        advisory.requires_human_review = True
        advisory.diagnostics["model"] = "D-policy-anomaly-advisory-only"
        return advisory
