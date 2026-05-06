"""Censored Binomial Lattice for SV — v2.0 附录 C / Chen-Wang 2015 Algorithm 1.

Used to value a long-term contract as a call option on the spot price under
a Stochastic Volatility model. Returned `option_value` is the fair premium:
  option_value > broker price → 签合约划算
  option_value < broker price → 走现货
"""
from __future__ import annotations

import numpy as np


def censored_binomial_lattice_sv(
    pi_0: float,
    sigma_0: float,
    kappa: float,
    theta: float,
    delta: float,
    T: float,
    n: int,
    r: float,
    strike: float,
) -> float:
    """SV-model lattice price of a European call.

    Parameters
    ----------
    pi_0 : current spot price (元/MWh)
    sigma_0 : current volatility
    kappa : volatility mean-reversion speed
    theta : long-run volatility
    delta : volatility-of-volatility (kept for API stability; the deterministic
            sigma path here doesn't use it — full 2-D lattice would)
    T : option tenor (years)
    n : number of discretization steps
    r : risk-free rate (annualized)
    strike : long-term contract strike (元/MWh)
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    dt = T / n
    r_disc = float(np.exp(r * dt))

    log_pi = float(np.log(pi_0))
    sigma_path = np.zeros(n + 1)
    sigma_path[0] = sigma_0
    for k in range(n):
        sigma_path[k + 1] = sigma_path[k] + kappa * (theta - sigma_path[k]) * dt

    lattice = np.zeros((n + 1, n + 1))
    Q = np.zeros((n + 1, n + 1))
    Q[0, 0] = 1.0
    lattice[0, 0] = log_pi

    for k in range(n):
        sig = float(sigma_path[k + 1])
        if sig <= 0:
            sig = 1e-8
        step = sig * np.sqrt(dt)
        drift = (r - 0.5 * sig**2) * dt

        for i in range(k + 1):
            X_curr = lattice[k, i]
            J = np.round(X_curr / step)
            X_up = (J + 1) * step + drift
            X_dn = (J - 1) * step + drift
            K = J * step - X_curr

            q_up_raw = (Q[k, i] / 2.0) * (1.0 + K / step)
            q_up = float(np.clip(q_up_raw, 0.0, Q[k, i]))
            q_dn = Q[k, i] - q_up

            lattice[k + 1, i] = X_up
            lattice[k + 1, i + 1] = X_dn
            Q[k + 1, i] += q_up
            Q[k + 1, i + 1] += q_dn

    payoffs = np.maximum(np.exp(lattice[n]) - strike, 0.0)
    option_value = float(np.sum(Q[n] * payoffs) / (r_disc**n))
    return option_value
