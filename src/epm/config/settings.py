"""Project-wide paths and defaults."""
from __future__ import annotations

import os
from dataclasses import dataclass


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass(frozen=True)
class Settings:
    project_root: str = PROJECT_ROOT
    data_dir: str = os.path.join(PROJECT_ROOT, "data")
    artifacts_dir: str = os.path.join(PROJECT_ROOT, "artifacts")
    runs_dir: str = os.path.join(PROJECT_ROOT, "runs")

    # AutoResearch — Walk-Forward (v2.0 §6.3)
    train_window_days: int = 365
    val_window_days: int = 23   # T-30 to T-7
    holdout_window_days: int = 7  # T-7 to T-1, 每周才用一次

    # Robust MDP (v2.0 §4.5.1)
    n_macro_periods: int = 8    # 时段段数 (8 段每段 3h)


SETTINGS = Settings()
