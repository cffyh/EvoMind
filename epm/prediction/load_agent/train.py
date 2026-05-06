"""Load forecasting — quantile regression head returning P10/P25/P50/P75/P90.

AutoResearch may rewrite this file freely within the constraints listed in
`program.md`. The downstream contract is `predict.py:predict_load_distribution`,
which must keep returning a dict of quantile arrays.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


QUANTILES: tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90)


@dataclass
class LoadModel:
    """Wrapper holding fitted quantile heads + feature schema."""
    estimators: dict[float, Any]   # quantile -> fitted estimator
    feature_cols: list[str]
    meta: dict


def train(features: pd.DataFrame, target_col: str = "load") -> LoadModel:
    """Train one quantile head per `QUANTILES` level.

    Stub: AutoResearch fills in the actual estimator (LightGBM with quantile
    objective, neural quantile head, etc.). Keep the return shape stable.
    """
    raise NotImplementedError(
        "load_agent.train: implement quantile regression — see program.md priorities"
    )
