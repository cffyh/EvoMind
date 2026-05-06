from epm.autoresearch.walk_forward import walk_forward_splits


def test_no_overlap_and_holdout_after_val():
    days = [f"2025-{m:02d}-{d:02d}" for m in (1, 2, 3) for d in range(1, 29)]
    days = sorted(set(days))
    splits = list(walk_forward_splits(days, train_window_days=30, val_window_days=7, holdout_window_days=3, step_days=7))
    assert splits, "expected at least one split"
    for s in splits:
        # ordering: train.end < val.start <= val.end < holdout.start <= holdout.end
        assert s.train_end < s.val_start
        assert s.val_end < s.holdout_start
        assert s.holdout_start <= s.holdout_end


def test_anchor_steps_by_step_days():
    days = [f"2025-01-{d:02d}" for d in range(1, 32)]
    splits = list(walk_forward_splits(days, train_window_days=10, val_window_days=3, holdout_window_days=2, step_days=3))
    assert len(splits) >= 2
    # the val_end should advance by step_days between consecutive splits
    delta = (splits[1].val_end > splits[0].val_end)
    assert delta
