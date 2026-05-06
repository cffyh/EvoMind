"""Common interface for the A–E model库 — v2.0 §4.4.

Every model takes a `SPInputs` (or its subclass), returns a `ModelOutput`
with a fully populated `q_da` (and optionally `p_da`). Anything beyond
this signature counts as骨架修改 and requires human review.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from epm.decision.stochastic_program import SPInputs


@dataclass
class ModelOutput:
    q_da: np.ndarray
    p_da: np.ndarray | None = None
    diagnostics: dict = field(default_factory=dict)
    requires_human_review: bool = False


class ModelInterface(Protocol):
    name: str

    def decide(self, inputs: SPInputs) -> ModelOutput: ...
