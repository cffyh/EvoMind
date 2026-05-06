"""Experiment orchestration — wires together backtest + ratchet + scanner.

Usage:
    from epm.autoresearch.runner import run_experiment
    decision = run_experiment(
        baseline_strategy=baseline_fn,
        challenger_strategy=candidate_fn,
        actual=df_actual,
        rules=GUANGDONG,
    )
    if decision.accept:
        # commit
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from epm.backtest import BacktestEngine, BacktestRun
from epm.config import MarketRules

from .ratchet import MetricSnapshot, RatchetGate, RatchetDecision
from .static_scanner import scan_for_leakage, ScanFinding


@dataclass
class ExperimentResult:
    decision: RatchetDecision
    baseline_run: BacktestRun
    candidate_run: BacktestRun
    leakage_findings: list[ScanFinding]


def _snapshot(run: BacktestRun, *, extreme_mask: pd.Series | None = None) -> MetricSnapshot:
    by_period = run.by_period
    cost_mean = -float(by_period["profit"].mean())
    cvar = run.summary["cvar"]
    deviation_rate = run.summary["deviation_rate"]

    if extreme_mask is not None and extreme_mask.any():
        ext_periods = by_period[by_period["target_day"].isin(extreme_mask[extreme_mask].index)]
        extreme_cost_mean = -float(ext_periods["profit"].mean()) if len(ext_periods) else cost_mean
    else:
        extreme_cost_mean = cost_mean

    declared = by_period["strategy_declary_load"].to_numpy()
    stability = float(np.mean(np.abs(np.diff(declared)))) if declared.size > 1 else 0.0

    return MetricSnapshot(
        cost_mean=cost_mean,
        cvar_95=cvar,
        deviation_rate=deviation_rate,
        extreme_day_cost_mean=extreme_cost_mean,
        stability_index=stability,
    )


def run_experiment(
    *,
    baseline_strategy,
    challenger_strategy,
    actual: pd.DataFrame,
    rules: MarketRules,
    scan_paths: list[str] | None = None,
    extreme_mask: pd.Series | None = None,
) -> ExperimentResult:
    leakage = scan_for_leakage(scan_paths) if scan_paths else []
    if leakage:
        # auto-revert: do not even backtest
        return ExperimentResult(
            decision=RatchetDecision(
                accept=False,
                reasons_pass=[],
                reasons_fail=[f"leakage scanner: {len(leakage)} hits"],
            ),
            baseline_run=BacktestRun(pd.DataFrame(), pd.DataFrame(), {}),
            candidate_run=BacktestRun(pd.DataFrame(), pd.DataFrame(), {}),
            leakage_findings=leakage,
        )

    engine = BacktestEngine(rules=rules)
    baseline_run = engine.run(actual, baseline_strategy)
    candidate_run = engine.run(actual, challenger_strategy)

    baseline_snap = _snapshot(baseline_run, extreme_mask=extreme_mask)
    candidate_snap = _snapshot(candidate_run, extreme_mask=extreme_mask)
    decision = RatchetGate().decide(baseline_snap, candidate_snap)

    return ExperimentResult(
        decision=decision,
        baseline_run=baseline_run,
        candidate_run=candidate_run,
        leakage_findings=[],
    )
