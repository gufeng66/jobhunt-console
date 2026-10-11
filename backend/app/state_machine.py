from dataclasses import dataclass
from datetime import datetime

STATUSES = (
    "communicated",
    "resume_requested",
    "interview",
    "offered",
    "rejected",
    "withdrawn",
)
IN_PROGRESS = frozenset({"communicated", "resume_requested", "interview"})
JOB_TYPES = frozenset({"实习", "校招"})
CHANNELS = frozenset({"BOSS", "官网", "内推", "其他"})


class RuleError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


def check_transition(current: str, target: str) -> None:
    if current == target:
        raise RuleError("状态未变化")
    if current in ("rejected", "withdrawn"):
        raise RuleError("该状态不能再改")
    if current == "offered":
        if target != "withdrawn":
            raise RuleError("录用只能改为已放弃")
        return
    if current not in IN_PROGRESS or target not in STATUSES:
        raise RuleError("该状态不能再改")


def check_changed_at(changed_at: datetime, previous: datetime, now: datetime) -> None:
    if changed_at < previous:
        raise RuleError("时间不能早于上一条")
    if changed_at > now:
        raise RuleError("时间不能晚于现在")


@dataclass
class Log:
    from_status: str | None
    to_status: str
    changed_at: datetime


def initial_log(status: str, applied_at: datetime, status_at: datetime | None, now: datetime) -> Log:
    if status not in STATUSES:
        raise RuleError("无效状态")
    if applied_at.date() > now.date():
        raise RuleError("投递日不能晚于今天")
    if status == "communicated":
        return Log(None, status, applied_at)
    if status_at is None:
        raise RuleError("请填写状态发生时间")
    if status_at < applied_at:
        raise RuleError("状态时间不能早于投递日")
    if status_at > now:
        raise RuleError("时间不能晚于现在")
    return Log(None, status, status_at)


@dataclass
class AppliedAtEdit:
    move_first_log_to: datetime | None
    update_last_status_at: bool


def edit_applied_at(old: datetime, new: datetime, logs: list[Log], now: datetime) -> AppliedAtEdit:
    if not logs or logs[0].from_status is not None:
        raise RuleError("缺少创建流水")
    if new.date() > now.date():
        raise RuleError("投递日不能晚于今天")
    first = logs[0]
    if first.changed_at == old:
        if len(logs) > 1 and new > logs[1].changed_at:
            raise RuleError("投递日不能晚于下一条流水")
        return AppliedAtEdit(new, len(logs) == 1)
    if new > first.changed_at:
        raise RuleError("投递日不能晚于第一条流水")
    return AppliedAtEdit(None, False)
