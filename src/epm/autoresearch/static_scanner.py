"""Pre-commit static scanner — v2.0 §7.3.1.

Catches common未来信息泄漏 patterns before they reach the棘轮 gate.
The complementary runtime check lives in `epm/data/validators.py`.

Patterns scanned (regex-based — fast, no AST round-trip):
  - `.shift(...)` calls with negative shifts (forward-looking)
  - reads of `actual_*_settle_*` without preceding `shift(`
  - imports from `data/actual_load_price_data.csv` outside `evaluate.py`
  - hard-coded future dates beyond `decision_day`
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass


@dataclass
class ScanFinding:
    file: str
    line: int
    pattern: str
    snippet: str


# Each pattern: (label, regex). Regexes are deliberately conservative
# (false-positives are cheap; false-negatives are expensive).
_PATTERNS: list[tuple[str, str]] = [
    ("negative-shift", r"\.shift\s*\(\s*-\s*\d"),
    ("raw-settle-read", r"actual_(day_ahead|realtime)_settle_elec_price"),
    ("raw-actual-load", r"actual_total_load(?!_info)"),
    ("realtime-node-read", r"actual_realtime_node_elec_price"),
    ("future-date", r"target_day\s*>\s*[\"\']\d{4}-\d{2}-\d{2}[\"\']"),
]


def scan_for_leakage(
    paths: list[str],
    *,
    allowlist_files: tuple[str, ...] = (
        "evaluate.py",
        "src_legacy",
        "src/",
        "epm/data/loader.py",
        "epm/data/feature_store.py",
        "epm/backtest/",
        "epm/autoresearch/static_scanner.py",  # the patterns themselves
    ),
) -> list[ScanFinding]:
    """Scan source files under `paths` for leakage patterns.

    `allowlist_files` are paths where it's legal to *read* settlement /
    actual columns directly (because the sites that consume these
    explicitly handle the time lag).
    """
    findings: list[ScanFinding] = []
    for root in paths:
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if not fn.endswith(".py"):
                    continue
                full = os.path.join(dirpath, fn)
                if any(allow in full for allow in allowlist_files):
                    continue
                try:
                    with open(full, "r", encoding="utf-8") as fp:
                        for lineno, line in enumerate(fp, start=1):
                            for label, pat in _PATTERNS:
                                if re.search(pat, line):
                                    findings.append(
                                        ScanFinding(
                                            file=full,
                                            line=lineno,
                                            pattern=label,
                                            snippet=line.rstrip(),
                                        )
                                    )
                except OSError:
                    continue
    return findings
