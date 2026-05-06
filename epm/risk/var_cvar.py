"""VaR / CVaR utilities — losses are positive, gains negative."""
from __future__ import annotations

import numpy as np


def value_at_risk(losses: np.ndarray, alpha: float = 0.95) -> float:
    """The α-VaR is the α-quantile of the loss distribution."""
    losses = np.asarray(losses, dtype=float)
    if losses.size == 0:
        return 0.0
    return float(np.quantile(losses, alpha))


def conditional_value_at_risk(losses: np.ndarray, alpha: float = 0.95) -> float:
    """CVaR = E[L | L >= VaR_α]. Uses Rockafellar-Uryasev form."""
    losses = np.asarray(losses, dtype=float)
    if losses.size == 0:
        return 0.0
    var = value_at_risk(losses, alpha)
    tail = losses[losses >= var]
    return float(tail.mean()) if tail.size else float(var)
