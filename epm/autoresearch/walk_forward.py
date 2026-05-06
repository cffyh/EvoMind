"""Walk-Forward 滚动验证 — v2.0 §6.3.

Strict time-ordered splits, no random shuffling:

    训练： T-365  ~  T-30
    验证： T-30   ~  T-7      (Agent reads this every iteration)
    留存： T-7    ~  T-1      (hidden from Agent, used once a week)

Generator yields one Split per anchor day (sliding window).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterator

import pandas as pd

from epm.config import SETTINGS


@dataclass(frozen=True)
class Split:
    train_start: str
    train_end: str
    val_start: str
    val_end: str
    holdout_start: str
    holdout_end: str

    def as_dict(self) -> dict:
        return self.__dict__


def walk_forward_splits(
    days: list[str] | pd.Index,
    *,
    train_window_days: int | None = None,
    val_window_days: int | None = None,
    holdout_window_days: int | None = None,
    step_days: int = 7,
) -> Iterator[Split]:
    """Slide a Walk-Forward window across `days`, stepping by `step_days`.

    Defaults are read from `SETTINGS`. The first usable anchor is the day
    on which (train_window + val_window + holdout_window) days fit before it.
    """
    train_w = train_window_days or SETTINGS.train_window_days
    val_w = val_window_days or SETTINGS.val_window_days
    hold_w = holdout_window_days or SETTINGS.holdout_window_days

    sorted_days = sorted(pd.to_datetime(d) for d in days)
    if not sorted_days:
        return

    min_anchor = sorted_days[0] + timedelta(days=train_w + val_w + hold_w)
    last_anchor = sorted_days[-1]

    cur = min_anchor
    while cur <= last_anchor:
        train_end = cur - timedelta(days=val_w + hold_w + 1)
        train_start = train_end - timedelta(days=train_w - 1)
        val_end = cur - timedelta(days=hold_w + 1)
        val_start = val_end - timedelta(days=val_w - 1)
        holdout_end = cur - timedelta(days=1)
        holdout_start = holdout_end - timedelta(days=hold_w - 1)

        yield Split(
            train_start=train_start.strftime("%Y-%m-%d"),
            train_end=train_end.strftime("%Y-%m-%d"),
            val_start=val_start.strftime("%Y-%m-%d"),
            val_end=val_end.strftime("%Y-%m-%d"),
            holdout_start=holdout_start.strftime("%Y-%m-%d"),
            holdout_end=holdout_end.strftime("%Y-%m-%d"),
        )
        cur += timedelta(days=step_days)
