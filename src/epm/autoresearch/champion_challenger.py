"""Champion-Challenger 上线机制 — v2.0 §6.5.

Three-stage gating before any new strategy reaches full traffic:

    Stage 1: 影子盘 (≥ 14 天) — Challenger runs in shadow vs Champion.
                              All 5 ratchet metrics must continuously beat Champion.
    Stage 2: 小额实盘 (≥ 30 天) — 10–20% of spot exposure routed to Challenger.
                              Primary metric must not regress.
    Stage 3: 切换 (人工) — Trading + Risk + Tech sign-off before promotion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class Stage(str, Enum):
    SHADOW = "shadow"
    SMALL_LIVE = "small_live"
    PROMOTION = "promotion"


@dataclass
class StageRecord:
    stage: Stage
    started_at: datetime
    ended_at: datetime | None = None
    pass_count: int = 0
    fail_count: int = 0
    notes: str = ""


@dataclass
class ChampionChallenger:
    challenger_id: str
    champion_id: str
    history: List[StageRecord] = field(default_factory=list)

    SHADOW_MIN_DAYS = 14
    SMALL_LIVE_MIN_DAYS = 30

    def start_stage(self, stage: Stage, when: datetime | None = None) -> None:
        rec = StageRecord(stage=stage, started_at=when or datetime.utcnow())
        self.history.append(rec)

    def record_outcome(self, passed: bool, note: str = "") -> None:
        if not self.history:
            raise RuntimeError("no stage in progress; call start_stage first")
        rec = self.history[-1]
        if passed:
            rec.pass_count += 1
        else:
            rec.fail_count += 1
        if note:
            rec.notes = f"{rec.notes}\n{note}".strip()

    def can_advance(self) -> bool:
        if not self.history:
            return False
        rec = self.history[-1]
        if rec.fail_count > 0:
            return False
        if rec.stage is Stage.SHADOW:
            return rec.pass_count >= self.SHADOW_MIN_DAYS
        if rec.stage is Stage.SMALL_LIVE:
            return rec.pass_count >= self.SMALL_LIVE_MIN_DAYS
        if rec.stage is Stage.PROMOTION:
            return False  # human sign-off required
        return False
