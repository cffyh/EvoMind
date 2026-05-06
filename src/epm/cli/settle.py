"""日终结算复盘 CLI — D+1 入口.

Pulls actual settlement, runs `BacktestEngine` over D, writes per-period
results, and triggers AutoResearch background iteration.
"""
from __future__ import annotations

import argparse


def main() -> int:
    p = argparse.ArgumentParser(description="EPM settlement / D+1 review")
    p.add_argument("--target-day", required=True, help="Operating day D")
    p.add_argument("--province", default="GD")
    args = p.parse_args()

    print(f"[stub] settling {args.province} day {args.target_day}")
    print("[stub] will trigger AutoResearch ratchet pass post-settlement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
