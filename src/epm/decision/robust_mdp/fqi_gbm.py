"""Fitted Q Iteration with Gradient Boosted Trees — v2.0 附录 D.

Batch RL approach (Ernst-Geurts-Wehenkel 2005) recommended for the
small-data electricity setting (4–8K samples). 1–2 数量级 more
data-efficient than DQN, naturally handles the strong feature
interactions and seasonality of electricity data.

Distillation path (v2.0 §4.5.6):
  M5–M9: FQI-GBM (this file)
  M10+: Linear Q + Polynomial Features + LSTD (closed form, interpretable)
  M18+: 神经网络 — only after 100K+ samples accumulated cross-province
"""
from __future__ import annotations

from typing import List

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

from .action import ACTION_SPACE


class FittedQIterationGBM:
    """Q(s, a) approximator via stacked GBMs over batched transitions."""

    def __init__(
        self,
        action_space: list | None = None,
        gamma: float = 0.95,
        max_iterations: int = 100,
        gbm_params: dict | None = None,
        convergence_tol: float = 1e-2,
    ):
        self.action_space = action_space or ACTION_SPACE
        self.gamma = gamma
        self.max_iter = max_iterations
        self.gbm_params = gbm_params or dict(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            min_samples_leaf=20,
        )
        self.convergence_tol = convergence_tol
        self.q_models: List[GradientBoostingRegressor] = []

    def fit(
        self,
        states: np.ndarray,
        actions: np.ndarray,
        rewards: np.ndarray,
        next_states: np.ndarray,
        terminals: np.ndarray,
    ) -> None:
        sa_features = self._build_sa_features(states, actions)
        targets = rewards.copy()

        for iteration in range(self.max_iter):
            model = GradientBoostingRegressor(**self.gbm_params)
            model.fit(sa_features, targets)
            self.q_models.append(model)

            next_q_max = self._compute_max_q(next_states, model)
            new_targets = rewards + self.gamma * (1.0 - terminals) * next_q_max

            if iteration > 0:
                delta = float(np.max(np.abs(new_targets - targets)))
                if delta < self.convergence_tol:
                    break
            targets = new_targets

    def _build_sa_features(self, states: np.ndarray, actions: np.ndarray) -> np.ndarray:
        action_oh = np.eye(len(self.action_space))[actions]
        return np.hstack([states, action_oh])

    def _compute_max_q(self, states: np.ndarray, model: GradientBoostingRegressor) -> np.ndarray:
        N = len(states)
        K = len(self.action_space)
        q_values = np.zeros((N, K))
        for k in range(K):
            actions_k = np.full(N, k, dtype=int)
            sa = self._build_sa_features(states, actions_k)
            q_values[:, k] = model.predict(sa)
        return q_values.max(axis=1)

    def policy(self, state: np.ndarray) -> int:
        if not self.q_models:
            raise RuntimeError("FQI not yet fit")
        model = self.q_models[-1]
        K = len(self.action_space)
        q_vals = np.zeros(K)
        for k in range(K):
            sa = self._build_sa_features(state[None], np.array([k], dtype=int))
            q_vals[k] = float(model.predict(sa)[0])
        return int(np.argmax(q_vals))
