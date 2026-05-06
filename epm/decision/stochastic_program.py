"""Two-stage stochastic program骨架 — v2.0 §4.1.

骨架冻结：
- 决策变量、目标函数、约束集合的形式由本文件固定
- AutoResearch 只能调 `epm/data/scenarios.py` 与 `control_by_model/models/*`
  里 model 内部参数 (场景数 / CVaR 阈值 / 平滑权重 ...)
- 任何对此处骨架的修改都必须经人工评审

The objective:
    min  Σ_t π_t^DA · q_t^DA
       + E_ω [ Σ_t π_{t,ω}^RT · q_{t,ω}^RT
              + λ · Penalty(q_t^DA, q_{t,ω}^RT, L_{t,ω}) ]
    s.t. q_t^DA + q_{t,ω}^RT + q_t^LT  =  L_{t,ω} + δ_{t,ω}  ∀ t,ω  (balance)
         p_min ≤ p_t^DA ≤ p_max                                     (compliance)
         CVaR_α(TotalCost)  ≤  C_max                                (risk, soft)
         |q_t^DA − q_{t-1}^DA|  ≤  Δ_max                            (smoothness, soft)

We deliberately leave solver choice open. Reference implementations:
- pyomo + gurobi/cplex/cbc (production)
- scipy.optimize.linprog (LP-only, baseline)
- Hand-rolled closed form (when penalty is piecewise linear in q^DA only)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from epm.config import MarketRules
from epm.data.scenarios import JointScenario


@dataclass
class SPInputs:
    rules: MarketRules
    scenarios: list[JointScenario]
    lt_quota: np.ndarray            # shape (T,) — 已签中长期合约电量曲线
    cvar_limit: float | None = None
    smoothness_delta_max: float | None = None
    penalty_weight: float = 1.0     # λ 在目标函数中的权重


@dataclass
class SPSolution:
    q_da: np.ndarray                # shape (T,) — 日前申报量（决策变量）
    p_da: np.ndarray | None         # shape (T,) — 仅当 mode = quantity_price 时
    expected_cost: float
    cvar: float
    objective: float
    metadata: dict = field(default_factory=dict)


def solve(inputs: SPInputs) -> SPSolution:
    """Solve the two-stage SP under the supplied scenarios.

    Stub: production version should call pyomo/gurobi. Until the solver is
    wired up, downstream callers should depend on this signature, not
    on any solver-specific object.
    """
    raise NotImplementedError(
        "stochastic_program.solve — wire up pyomo/gurobi (M5 deliverable)."
    )
