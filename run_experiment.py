"""
AutoResearch 实验记录器
包装 evaluate.py 的评分逻辑，每次运行自动追加结果到 experiments.md。
NEW BEST 时自动更新 CHANGELOG.md 并 commit + push。

用法:
    python3 run_experiment.py --desc "交互特征：日前出清价×正比率"
"""

import argparse
import re
import os
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "experiments.md")
CHANGELOG_FILE = os.path.join(BASE_DIR, "CHANGELOG.md")

HEADER = """# Experiments

| Round | Time | Train | Val | Best | Description |
|------:|------|------:|----:|:----:|-------------|
"""


def parse_experiments():
    if not os.path.exists(LOG_FILE):
        return 0, 0.0, []

    with open(LOG_FILE) as f:
        content = f.read()

    lines = []
    max_round = 0
    best_val = 0.0

    for line in content.strip().split("\n"):
        m = re.match(r'^\|\s*(\d+)\s*\|.*\|\s*([\d.]+)\s*\|', line)
        if m:
            lines.append(line)
            r = int(m.group(1))
            v = float(m.group(2))
            max_round = max(max_round, r)
            best_val = max(best_val, v)

    return max_round, best_val, lines


def run_evaluation():
    from evaluate import prepare_actual_data, compute_score, TRAIN_START, TRAIN_END, VAL_START, VAL_END
    from strategy import run_strategy

    df_actual = prepare_actual_data()
    df_strategy = run_strategy(TRAIN_START, VAL_END)

    train_result = compute_score(df_actual, df_strategy, TRAIN_START, TRAIN_END)
    val_result = compute_score(df_actual, df_strategy, VAL_START, VAL_END)

    return train_result["score"], val_result["score"]


def update_changelog(round_num, val_score, desc):
    if not os.path.exists(CHANGELOG_FILE):
        content = "# Changelog\n"
    else:
        with open(CHANGELOG_FILE) as f:
            content = f.read()

    new_entry = f"\n## Round {round_num} — val_score: {val_score:.4f}\n\n- {desc}\n"

    content = content.replace("# Changelog\n", f"# Changelog\n{new_entry}", 1)

    with open(CHANGELOG_FILE, "w") as f:
        f.write(content)


def auto_commit_and_push(round_num, val_score, desc):
    files = ["strategy.py", "experiments.md", "CHANGELOG.md", "run_experiment.py"]
    subprocess.run(["git", "add"] + files, cwd=BASE_DIR)
    msg = f"Round {round_num}: {desc} (val_score {val_score:.4f})"
    result = subprocess.run(["git", "commit", "-m", msg], cwd=BASE_DIR, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"--- git commit: {msg} ---")
        push_result = subprocess.run(["git", "push", "origin"], cwd=BASE_DIR, capture_output=True, text=True)
        if push_result.returncode == 0:
            print("--- git push: OK ---")
        else:
            print(f"--- git push failed: {push_result.stderr.strip()} ---")
    else:
        print(f"--- git commit failed: {result.stderr.strip()} ---")


def main():
    parser = argparse.ArgumentParser(description="Run experiment and log results")
    parser.add_argument("--desc", type=str, default="", help="Experiment description")
    args = parser.parse_args()

    max_round, prev_best, existing_lines = parse_experiments()
    round_num = max_round + 1

    train_score, val_score = run_evaluation()

    is_best = val_score > prev_best
    ts = datetime.now().strftime("%m-%d %H:%M")
    best_mark = "Y" if is_best else ""

    new_line = f"| {round_num} | {ts} | {train_score:.4f} | {val_score:.4f} | {best_mark} | {args.desc} |"

    existing_lines.append(new_line)
    with open(LOG_FILE, "w") as f:
        f.write(HEADER.lstrip())
        for line in existing_lines:
            f.write(line + "\n")

    print(f"=== Evaluation Results ===")
    print(f"train_score: {train_score:.6f}")
    print(f"val_score:   {val_score:.6f}")

    if is_best:
        print(f"--- Round {round_num} | NEW BEST (prev: {prev_best:.4f}) | logged to experiments.md ---")
        update_changelog(round_num, val_score, args.desc)
        auto_commit_and_push(round_num, val_score, args.desc)
    else:
        print(f"--- Round {round_num} | best: {prev_best:.4f} | logged to experiments.md ---")


if __name__ == "__main__":
    main()
