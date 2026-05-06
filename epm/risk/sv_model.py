"""Stochastic Volatility model — v2.0 §5.2.

The SV diffusion (continuous form):
    dπ(t) = μ·π·dt + σ(t)·π·dW(t)
    dσ(t) = κ·(θ−σ(t))·dt + δ·√σ(t)·dZ(t)

Critical operational rule (§5.2.2): SV params **must** be fit independently
per (province, month, macro_period). Pooling across these dimensions
under-estimates extreme tail risk.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class SVParams:
    mu: float          # 价格漂移
    kappa: float       # 波动率均值回归速度
    theta: float       # 长期波动率
    delta: float       # 波动率的波动率
    sigma_0: float     # 当前波动率初值


def gbm_vs_sv_test(prices: Iterable[float], alpha: float = 0.05) -> dict:
    """v2.0 §5.2.1 — Shapiro-Wilk + Ljung-Box on log-returns.

    Returns a dict with both p-values and a `must_use_sv` flag. Either test
    failing means GBM is rejected and SV is mandatory.
    """
    arr = np.asarray(list(prices), dtype=float)
    arr = arr[np.isfinite(arr) & (arr > 0)]
    if arr.size < 30:
        return {"shapiro_p": float("nan"), "ljungbox_p": float("nan"), "must_use_sv": True, "n": int(arr.size)}

    log_ret = np.diff(np.log(arr))

    try:
        from scipy import stats  # type: ignore
        sw = stats.shapiro(log_ret)
        shapiro_p = float(sw.pvalue)
    except Exception:
        shapiro_p = float("nan")

    try:
        from statsmodels.stats.diagnostic import acorr_ljungbox  # type: ignore
        lb = acorr_ljungbox(log_ret, lags=[10], return_df=True)
        ljungbox_p = float(lb["lb_pvalue"].iloc[0])
    except Exception:
        ljungbox_p = float("nan")

    must_use_sv = (
        not (np.isfinite(shapiro_p) and shapiro_p > alpha)
        or not (np.isfinite(ljungbox_p) and ljungbox_p > alpha)
    )
    return {
        "shapiro_p": shapiro_p,
        "ljungbox_p": ljungbox_p,
        "must_use_sv": bool(must_use_sv),
        "n": int(arr.size),
    }


def estimate_sv_params(prices: Iterable[float]) -> SVParams:  # pragma: no cover — TODO M5
    """Calibrate SV parameters via QMLE / particle filter / GMM.

    Stub: implement with `arch` package (HARSV) or hand-rolled Kalman filter.
    Until then, the rest of the pipeline can take SVParams from a config.
    """
    raise NotImplementedError("estimate_sv_params — see v2.0 §5.2.2")
