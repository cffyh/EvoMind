"""月度复盘 CLI — 月初执行.

Per v2.0 §5.3.1: independent of the daily loop. Outputs the recommended
LT contract share for the next month under three scenarios (保守/中性/激进).
**Advisory only** — never auto-executes.
"""
from __future__ import annotations

import argparse


def main() -> int:
    p = argparse.ArgumentParser(description="EPM monthly LT-share review")
    p.add_argument("--month", required=True, help="Target month, e.g. 2026-06")
    p.add_argument("--province", default="GD")
    args = p.parse_args()

    print(f"[stub] running monthly review for {args.province} {args.month}")
    print("[stub] output is advisory; LT contracts remain a human decision.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
