from epm.autoresearch.ratchet import MetricSnapshot, RatchetGate, RatchetThresholds


def _snap(cost=100.0, cvar=200.0, dev=0.01, ext=110.0, stab=5.0):
    return MetricSnapshot(cost_mean=cost, cvar_95=cvar, deviation_rate=dev, extreme_day_cost_mean=ext, stability_index=stab)


def test_strict_improvement_passes():
    base = _snap()
    cand = _snap(cost=99.0, cvar=199.0, dev=0.009, ext=109.0, stab=5.0)
    decision = RatchetGate().decide(base, cand)
    assert decision.accept, decision.reasons_fail


def test_cvar_regression_blocks():
    base = _snap()
    cand = _snap(cost=99.0, cvar=210.0)  # CVaR up 5% > 2% tolerance
    decision = RatchetGate().decide(base, cand)
    assert not decision.accept
    assert any("CVaR" in r for r in decision.reasons_fail)


def test_deviation_cap_blocks():
    base = _snap()
    cand = _snap(cost=90.0, dev=0.03)  # over hard cap 0.02
    decision = RatchetGate().decide(base, cand)
    assert not decision.accept
    assert any("deviation" in r for r in decision.reasons_fail)


def test_extreme_day_regression_blocks():
    base = _snap()
    cand = _snap(cost=90.0, ext=130.0)  # +18% on extreme days
    decision = RatchetGate().decide(base, cand)
    assert not decision.accept


def test_cost_must_strictly_improve():
    base = _snap()
    cand = _snap(cost=99.7)  # only 0.3% improvement, below 0.5% threshold
    decision = RatchetGate().decide(base, cand)
    assert not decision.accept
