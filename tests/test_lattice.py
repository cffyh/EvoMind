"""Censored Binomial Lattice — basic sanity tests.

Two invariants we care about for an option价格:
  (1) deep ITM (strike well below spot) should price near intrinsic
  (2) deep OTM (strike well above spot) should price near zero
  (3) value is monotone non-increasing in strike
"""
import numpy as np

from epm.risk.lattice import censored_binomial_lattice_sv


def _price(strike: float) -> float:
    return censored_binomial_lattice_sv(
        pi_0=400.0,
        sigma_0=0.40,
        kappa=2.0,
        theta=0.40,
        delta=0.20,
        T=30 / 365,
        n=30,
        r=0.03,
        strike=strike,
    )


def test_deep_otm_near_zero():
    val = _price(strike=2000.0)
    assert val < 1.0


def test_monotone_decreasing_in_strike():
    strikes = [200, 300, 400, 500, 600, 800]
    prices = [_price(s) for s in strikes]
    assert all(prices[i] >= prices[i + 1] - 1e-6 for i in range(len(prices) - 1)), prices


def test_finite_and_nonneg():
    val = _price(strike=380.0)
    assert np.isfinite(val) and val >= 0
