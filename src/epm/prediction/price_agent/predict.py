from __future__ import annotations

import numpy as np
import pandas as pd

from .train import PriceModel, QUANTILES


def predict_price_distribution(
    model: PriceModel, features: pd.DataFrame
) -> dict[str, dict[float, np.ndarray]]:
    """Return {'da': {q: arr}, 'rt': {q: arr}}."""
    out: dict[str, dict[float, np.ndarray]] = {"da": {}, "rt": {}}
    for q in QUANTILES:
        out["da"][q] = np.asarray(model.da_estimators[q].predict(features[model.feature_cols]))
        out["rt"][q] = np.asarray(model.rt_estimators[q].predict(features[model.feature_cols]))
    return out
