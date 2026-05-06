"""Smoke test — every public module imports cleanly with no ML dependencies missing."""


def test_top_level_imports():
    import epm  # noqa: F401
    import epm.config  # noqa: F401
    import epm.data  # noqa: F401
    import epm.prediction  # noqa: F401
    import epm.risk  # noqa: F401
    import epm.decision  # noqa: F401
    from epm.decision.control_by_model import select_model, ModelChoice  # noqa: F401
    from epm.decision.control_by_model.models import ModelA, ModelB, ModelC, ModelD, ModelE  # noqa: F401
    from epm.decision.robust_mdp import build_state, FittedQIterationGBM, ACTION_SPACE  # noqa: F401
    import epm.supervision  # noqa: F401
    import epm.backtest  # noqa: F401
    import epm.autoresearch  # noqa: F401
    import epm.cli  # noqa: F401


def test_action_space_size():
    from epm.decision.robust_mdp import ACTION_SPACE
    assert len(ACTION_SPACE) == 7 * 5 * 3


def test_market_rules_lookup():
    from epm.config import get
    rules = get("GD")
    assert rules.lambda_0 == 0.20
    assert rules.n_periods_per_day == 24
