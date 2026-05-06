"""AutoResearch 改造层 — Karpathy 棘轮循环 + 电力场景五项改造 (v2.0 §6).

Multi-metric ratchet, walk-forward, extreme-day subset evaluation,
static leakage scanner, Champion-Challenger.
"""
from .ratchet import RatchetGate, RatchetDecision, MetricSnapshot
from .walk_forward import walk_forward_splits, Split
from .extreme_days import classify_extreme_days, ExtremeDayLabels
from .static_scanner import scan_for_leakage, ScanFinding
from .champion_challenger import ChampionChallenger, Stage

__all__ = [
    "RatchetGate",
    "RatchetDecision",
    "MetricSnapshot",
    "walk_forward_splits",
    "Split",
    "classify_extreme_days",
    "ExtremeDayLabels",
    "scan_for_leakage",
    "ScanFinding",
    "ChampionChallenger",
    "Stage",
]
