import numpy as np

from epm.risk.var_cvar import value_at_risk, conditional_value_at_risk


def test_var_known_quantile():
    losses = np.arange(101, dtype=float)  # 0..100
    assert value_at_risk(losses, alpha=0.95) == 95.0


def test_cvar_ge_var():
    rng = np.random.default_rng(0)
    losses = rng.standard_normal(10_000)
    var = value_at_risk(losses, alpha=0.95)
    cvar = conditional_value_at_risk(losses, alpha=0.95)
    assert cvar >= var


def test_empty_returns_zero():
    assert value_at_risk(np.array([]), alpha=0.9) == 0.0
    assert conditional_value_at_risk(np.array([]), alpha=0.9) == 0.0
