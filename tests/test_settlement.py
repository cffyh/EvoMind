"""Settlement is the load-bearing financial primitive — it must reproduce
the original `src_legacy/backtest_gd.py` outputs exactly under default
广东 rules, since the AutoResearch evaluator depends on those numbers.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src_legacy"))
from backtest_gd import BackTest  # type: ignore  # noqa: E402

from epm.config import GUANGDONG
from epm.backtest.settlement import settle_period


def _legacy(da, decl, rt, load):
    bt = BackTest(da, decl, rt, load, GUANGDONG.lambda_0, GUANGDONG.mu)
    profit, income, cost, _ = bt.get_dayahead_bid_profit()
    return profit, income, cost


def test_case_over_declare_when_rt_higher():
    da, rt, load, decl = 300.0, 400.0, 100.0, 130.0  # decl > load*(1+λ)=120
    legacy_profit, _, legacy_cost = _legacy(da, decl, rt, load)
    res = settle_period(GUANGDONG, da_price=da, rt_price=rt, declared_q=decl, realized_load=load)
    assert abs(res.profit - legacy_profit) < 1e-6
    assert abs(res.deviation_cost - legacy_cost) < 1e-6


def test_case_under_declare_when_da_higher():
    da, rt, load, decl = 400.0, 300.0, 100.0, 70.0  # decl < load*(1-λ)=80
    legacy_profit, _, legacy_cost = _legacy(da, decl, rt, load)
    res = settle_period(GUANGDONG, da_price=da, rt_price=rt, declared_q=decl, realized_load=load)
    assert abs(res.profit - legacy_profit) < 1e-6
    assert abs(res.deviation_cost - legacy_cost) < 1e-6


def test_case_no_penalty_inside_band():
    da, rt, load, decl = 300.0, 400.0, 100.0, 110.0  # within (1+λ)=120
    legacy_profit, _, legacy_cost = _legacy(da, decl, rt, load)
    res = settle_period(GUANGDONG, da_price=da, rt_price=rt, declared_q=decl, realized_load=load)
    assert res.deviation_cost == 0
    assert abs(res.profit - legacy_profit) < 1e-6
    assert legacy_cost == 0
