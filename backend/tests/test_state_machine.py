from datetime import datetime

import pytest

from app.state_machine import (
    IN_PROGRESS,
    AppliedAtEdit,
    Log,
    RuleError,
    check_changed_at,
    check_transition,
    edit_applied_at,
    initial_log,
)

NOW = datetime(2026, 10, 11, 12, 0, 0)
DAY = datetime(2026, 10, 1, 0, 0, 0)
LATER = datetime(2026, 10, 8, 0, 0, 0)


def test_in_progress_can_move_among_themselves():
    for src in IN_PROGRESS:
        for dst in IN_PROGRESS - {src}:
            check_transition(src, dst)


def test_in_progress_can_enter_any_terminal():
    for src in IN_PROGRESS:
        for dst in ("offered", "rejected", "withdrawn"):
            check_transition(src, dst)


def test_offered_can_become_withdrawn():
    check_transition("offered", "withdrawn")


def test_offered_cannot_return_to_in_progress():
    with pytest.raises(RuleError):
        check_transition("offered", "communicated")


@pytest.mark.parametrize("sealed", ["rejected", "withdrawn"])
def test_sealed_statuses_stay_sealed(sealed):
    with pytest.raises(RuleError):
        check_transition(sealed, "communicated")


def test_same_status_does_not_log():
    with pytest.raises(RuleError, match="状态未变化"):
        check_transition("interview", "interview")


def test_changed_at_before_previous_is_rejected():
    with pytest.raises(RuleError, match="早于上一条"):
        check_changed_at(DAY, LATER, NOW)


def test_changed_at_after_now_is_rejected():
    with pytest.raises(RuleError, match="晚于现在"):
        check_changed_at(datetime(2026, 10, 12), LATER, NOW)


def test_create_writes_one_log_with_empty_from_status():
    log = initial_log("communicated", DAY, None, NOW)
    assert log == Log(None, "communicated", DAY)


def test_other_status_before_applied_at_is_rejected():
    with pytest.raises(RuleError, match="早于投递日"):
        initial_log("interview", LATER, DAY, NOW)


def test_applied_at_cannot_pass_the_next_log():
    logs = [Log(None, "communicated", DAY), Log("communicated", "interview", LATER)]
    with pytest.raises(RuleError, match="下一条"):
        edit_applied_at(DAY, datetime(2026, 10, 9), logs, NOW)


def test_moving_the_only_log_updates_last_status_at():
    logs = [Log(None, "communicated", DAY)]
    edited = edit_applied_at(DAY, datetime(2026, 9, 1), logs, NOW)
    assert edited == AppliedAtEdit(datetime(2026, 9, 1), True)
