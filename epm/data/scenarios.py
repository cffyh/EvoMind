"""场景生成 — v2.0 §4.2.

The two-stage SP骨架 in `decision/stochastic_program.py` consumes a list
of (price_path, load_path) scenarios. AutoResearch is allowed to iterate
*these generators* freely; the SP骨架 itself stays frozen.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd


@dataclass
class JointScenario:
    """One sampled future path of (prices, loads) for a single decision day."""
    price_da: np.ndarray   # shape (T,) day-ahead price path
    price_rt: np.ndarray   # shape (T,) realtime price path
    load: np.ndarray       # shape (T,) realized load path
    weight: float = 1.0    # probability mass assigned to this scenario


def bootstrap_scenarios(
    history: pd.DataFrame,
    *,
    n_periods: int,
    n_scenarios: int = 200,
    seed: int | None = None,
) -> list[JointScenario]:
    """Bootstrap sampling — resample whole historical days.

    The most defensible baseline: preserves intra-day dependence structure
    by construction, no model risk. v2.0 §4.2.1 lists this as the
    interpretability winner among scenario-generation methods.
    """
    rng = np.random.default_rng(seed)
    days = sorted(history["target_day"].unique())
    if not days:
        return []

    scenarios: list[JointScenario] = []
    chosen = rng.choice(days, size=n_scenarios, replace=True)
    for d in chosen:
        day = history[history["target_day"] == d].sort_values("period")
        if len(day) != n_periods:
            continue
        scenarios.append(
            JointScenario(
                price_da=day["da_settle"].to_numpy(),
                price_rt=day["rt_settle"].to_numpy(),
                load=day["load"].to_numpy(),
                weight=1.0 / n_scenarios,
            )
        )
    return scenarios


def monte_carlo_scenarios(
    price_dist_sampler: Callable[[int], np.ndarray],
    load_dist_sampler: Callable[[int], np.ndarray],
    *,
    n_periods: int,
    n_scenarios: int = 500,
) -> list[JointScenario]:
    """Independent MC sampling — fast baseline.

    Caller passes per-period samplers; correlation between price and load
    is **not** captured here (use `copula_scenarios` for that).
    """
    scenarios = []
    for _ in range(n_scenarios):
        price = price_dist_sampler(n_periods)
        load = load_dist_sampler(n_periods)
        scenarios.append(
            JointScenario(price_da=price, price_rt=price, load=load, weight=1.0 / n_scenarios)
        )
    return scenarios


def reduce_scenarios(scenarios: list[JointScenario], *, k: int = 50) -> list[JointScenario]:
    """k-means style scenario reduction — v2.0 §4.2.2.

    Stub: returns the first k. Full implementation should cluster on
    flattened (price_da, price_rt, load) vectors and keep cluster medoids
    + reweight by cluster mass; extreme scenarios oversampled.
    """
    if len(scenarios) <= k:
        return scenarios
    return scenarios[:k]


def copula_scenarios(*args, **kwargs):  # pragma: no cover — TODO M5
    """Copula-based joint sampling — captures price/load/renewable dependence.

    Implement with `copulas` package or hand-rolled Gaussian/t-copula.
    """
    raise NotImplementedError("copula sampling — see v2.0 §4.2.1")


def diffusion_scenarios(*args, **kwargs):  # pragma: no cover — TODO M5+
    """Diffusion-based time-series generation — fat-tail friendly."""
    raise NotImplementedError("diffusion sampling — see v2.0 §4.2.1")
