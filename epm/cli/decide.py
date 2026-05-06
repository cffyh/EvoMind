"""日前申报 CLI — D-1 09:30 入口.

Sequence (per v2.0 §3.2 时序表):
  06:00  data pull
  07:00  load forecast
  07:30  price forecast
  08:30  Control-by-Model select + SP solve
  09:00  RiskGuard check
  09:15  human review (only if Model D selected)
  09:30  submit declaration
"""
from __future__ import annotations

import argparse


def main() -> int:
    p = argparse.ArgumentParser(description="EPM daily declaration runner")
    p.add_argument("--target-day", required=True, help="Operating day D (YYYY-MM-DD)")
    p.add_argument("--province", default="GD")
    p.add_argument("--dry-run", action="store_true", help="Don't actually submit")
    args = p.parse_args()

    print(f"[stub] running daily decide loop for {args.province} on {args.target_day}")
    print("[stub] this CLI will be wired up after the SP solver lands (M5).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
