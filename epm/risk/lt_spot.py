"""中长期 vs 现货比例决策 — v2.0 §4.1.4 + §5.3.

Two distinct uses:

1. `p_lt_max(...)` — buyer-side dual-flipped Chen-Yuan-Wang 2014 Eq.(2):
   the highest LT contract price worth signing under the current SV state.

2. `suggest_lt_ratio(...)` — monthly LT-share recommendation by realized
   volatility regime (high/mid/low). Output is advisory only; the actual
   LT contract decision stays human (per §5.3.2 重要警示).
"""
from __future__ import annotations

from enum import Enum

from epm.config import MarketRules


class VolRegime(str, Enum):
    HIGH = "high"
    MID = "mid"
    LOW = "low"


def p_lt_max(e_spot: float, sigma_spot: float, lambda_risk: float, e_spot_max: float) -> float:
    """Dual-flipped LT-price ceiling for a buyer.

    p_LT_max = min( E[π_spot] − λ·σ_spot,  E[π_spot_max] )

    Sign an LT contract only if broker price ≤ p_LT_max.
    """
    return float(min(e_spot - lambda_risk * sigma_spot, e_spot_max))


def classify_vol_regime(realized_vol: float, *, low_thresh: float, high_thresh: float) -> VolRegime:
    """Bucket realized vol into one of three regimes.

    Thresholds are province- and season-specific; calibrate from history.
    """
    if realized_vol >= high_thresh:
        return VolRegime.HIGH
    if realized_vol <= low_thresh:
        return VolRegime.LOW
    return VolRegime.MID


def suggest_lt_ratio(regime: VolRegime, rules: MarketRules) -> float:
    """Map regime to the §5.3.2 recommended LT share."""
    if regime is VolRegime.HIGH:
        return rules.lt_ratio_high_vol
    if regime is VolRegime.LOW:
        return rules.lt_ratio_low_vol
    return rules.lt_ratio_mid_vol
