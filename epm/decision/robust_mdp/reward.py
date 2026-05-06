"""Reward function — v2.0 §4.5.4 / 附录 D `compute_reward`.

r_t = −[ realized_cost_t
       + λ_dev · deviation_penalty_t
       + λ_cvar · cvar_violation_t ]

Three weights (1, λ_dev, λ_cvar) are **手工设定** per v2.0 §4.5.4 — do
not let the RL algorithm tune them. Defaults match 附录 D guidance.
"""
from __future__ import annotations


def compute_reward(
    realized_cost: float,
    deviation_pct: float,
    deviation_threshold: float,
    cvar_loss: float,
    cvar_limit: float,
    *,
    lambda_dev: float = 5.0,
    lambda_cvar: float = 2.0,
) -> float:
    deviation_penalty = max(0.0, abs(deviation_pct) - deviation_threshold)
    cvar_violation = max(0.0, cvar_loss - cvar_limit)
    return -(realized_cost + lambda_dev * deviation_penalty + lambda_cvar * cvar_violation)
