from __future__ import annotations

import numpy as np
import pandas as pd

from .train import LoadModel, QUANTILES


def predict_load_distribution(model: LoadModel, features: pd.DataFrame) -> dict[float, np.ndarray]:
    """Return {quantile: array of shape (n_rows,)} predictions."""
    out: dict[float, np.ndarray] = {}
    for q in QUANTILES:
        est = model.estimators.get(q)
        if est is None:
            raise KeyError(f"model missing quantile head q={q}")
        out[q] = np.asarray(est.predict(features[model.feature_cols]))
    return out
