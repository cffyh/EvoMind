from epm.config import GUANGDONG
from epm.risk.lt_spot import VolRegime, classify_vol_regime, p_lt_max, suggest_lt_ratio


def test_p_lt_max_takes_min_arm():
    # E[π_spot] - λ·σ = 380, E[π_spot_max] = 500 → expect 380
    assert p_lt_max(e_spot=400, sigma_spot=20, lambda_risk=1.0, e_spot_max=500) == 380.0
    # Reverse: σ very small so first arm dominates positively, but cap binds
    assert p_lt_max(e_spot=400, sigma_spot=20, lambda_risk=1.0, e_spot_max=370) == 370.0


def test_classify_vol_regime():
    assert classify_vol_regime(50, low_thresh=20, high_thresh=80) is VolRegime.MID
    assert classify_vol_regime(10, low_thresh=20, high_thresh=80) is VolRegime.LOW
    assert classify_vol_regime(90, low_thresh=20, high_thresh=80) is VolRegime.HIGH


def test_suggest_lt_ratio_uses_rules():
    assert suggest_lt_ratio(VolRegime.HIGH, GUANGDONG) == GUANGDONG.lt_ratio_high_vol
    assert suggest_lt_ratio(VolRegime.MID, GUANGDONG) == GUANGDONG.lt_ratio_mid_vol
    assert suggest_lt_ratio(VolRegime.LOW, GUANGDONG) == GUANGDONG.lt_ratio_low_vol
