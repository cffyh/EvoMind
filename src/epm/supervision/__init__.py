"""监督层 — 硬编码规则，AutoResearch Agent 不允许修改本目录任何文件.

Each commit changing files under `epm/supervision/` must go through human
review (enforced via CODEOWNERS / pre-commit hook in production).
"""
from .risk_guard import RiskGuard, GuardViolation
from .compliance import ComplianceChecker
from .meta_coordinator import MetaCoordinator, ConflictReport

__all__ = [
    "RiskGuard",
    "GuardViolation",
    "ComplianceChecker",
    "MetaCoordinator",
    "ConflictReport",
]
