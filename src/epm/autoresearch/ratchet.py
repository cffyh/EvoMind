"""多指标棘轮 — v2.0 §6.2.

不再单一 val_score 棘轮。一次 commit 必须满足 5 项条件，否则 git revert:
  1. 成本均值改善 > 0.5%
  2. CVaR_95 不显著退化（不超过基线 +2%）
  3. 偏差率不超过阈值
  4. 极端日子集表现不退化
  5. 策略稳定性指标不退化（相邻日报价变化幅度）
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MetricSnapshot:
    cost_mean: float
    cvar_95: float
    deviation_rate: float
    extreme_day_cost_mean: float
    stability_index: float    # e.g. mean abs diff between consecutive q_da
    extras: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RatchetThresholds:
    cost_min_improvement: float = 0.005       # 主指标 +0.5%
    cvar_max_regression: float = 0.02         # CVaR 不能比基线差 >2%
    deviation_rate_cap: float = 0.02          # 偏差率硬上限
    extreme_max_regression: float = 0.005     # 极端日子集 +0.5%
    stability_max_regression: float = 0.10    # 稳定性指标 +10%


@dataclass
class RatchetDecision:
    accept: bool
    reasons_pass: list[str]
    reasons_fail: list[str]


class RatchetGate:
    """All-pass-or-revert. Use one instance per autoresearch loop."""

    def __init__(self, thresholds: RatchetThresholds | None = None):
        self.t = thresholds or RatchetThresholds()

    def decide(self, baseline: MetricSnapshot, candidate: MetricSnapshot) -> RatchetDecision:
        passes: list[str] = []
        fails: list[str] = []

        # baseline cost is positive (it IS a cost). Improvement = lower cost.
        cost_rel = (baseline.cost_mean - candidate.cost_mean) / max(abs(baseline.cost_mean), 1e-9)
        if cost_rel >= self.t.cost_min_improvement:
            passes.append(f"cost improved {cost_rel:+.4f}")
        else:
            fails.append(f"cost improvement {cost_rel:+.4f} < {self.t.cost_min_improvement}")

        cvar_rel = (candidate.cvar_95 - baseline.cvar_95) / max(abs(baseline.cvar_95), 1e-9)
        if cvar_rel <= self.t.cvar_max_regression:
            passes.append(f"CVaR change {cvar_rel:+.4f} within tolerance")
        else:
            fails.append(f"CVaR regression {cvar_rel:+.4f} > {self.t.cvar_max_regression}")

        if candidate.deviation_rate <= self.t.deviation_rate_cap:
            passes.append(f"deviation rate {candidate.deviation_rate:.4f} within cap")
        else:
            fails.append(
                f"deviation rate {candidate.deviation_rate:.4f} > cap {self.t.deviation_rate_cap}"
            )

        ext_rel = (candidate.extreme_day_cost_mean - baseline.extreme_day_cost_mean) / max(
            abs(baseline.extreme_day_cost_mean), 1e-9
        )
        if ext_rel <= self.t.extreme_max_regression:
            passes.append(f"extreme-day cost change {ext_rel:+.4f} within tolerance")
        else:
            fails.append(
                f"extreme-day cost regression {ext_rel:+.4f} > {self.t.extreme_max_regression}"
            )

        stab_rel = (candidate.stability_index - baseline.stability_index) / max(
            abs(baseline.stability_index), 1e-9
        )
        if stab_rel <= self.t.stability_max_regression:
            passes.append(f"stability change {stab_rel:+.4f} within tolerance")
        else:
            fails.append(
                f"stability regression {stab_rel:+.4f} > {self.t.stability_max_regression}"
            )

        return RatchetDecision(accept=not fails, reasons_pass=passes, reasons_fail=fails)
