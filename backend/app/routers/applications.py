from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.models import Application, StatusLog, User
from app.state_machine import (
    CHANNELS,
    JOB_TYPES,
    Log,
    RuleError,
    check_changed_at,
    check_transition,
    edit_applied_at,
    initial_log,
)

router = APIRouter(prefix="/applications")
PAGE_SIZE = 20


class AppIn(BaseModel):
    company_name: str
    position_name: str
    job_type: str
    channel: str = "BOSS"
    status: str = "communicated"
    applied_at: datetime | None = None
    status_at: datetime | None = None
    city: str | None = None
    salary_range: str | None = None
    jd_text: str | None = None
    notes: str | None = None


class AppPatch(BaseModel):
    company_name: str | None = None
    position_name: str | None = None
    job_type: str | None = None
    channel: str | None = None
    city: str | None = None
    salary_range: str | None = None
    jd_text: str | None = None
    notes: str | None = None
    applied_at: datetime | None = None


class StatusIn(BaseModel):
    to_status: str
    changed_at: datetime | None = None
    note: str | None = None


def clock() -> datetime:
    return datetime.now().replace(microsecond=0)


def naive(value: datetime) -> datetime:
    return value.replace(tzinfo=None) if value.tzinfo else value


def fail(err: RuleError) -> None:
    raise HTTPException(422, err.detail)


def blank(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def dump(row: Application, with_logs: bool = False) -> dict:
    data = {
        "id": row.id,
        "company_name": row.company_name,
        "position_name": row.position_name,
        "job_type": row.job_type,
        "channel": row.channel,
        "city": row.city,
        "salary_range": row.salary_range,
        "jd_text": row.jd_text,
        "status": row.status,
        "applied_at": row.applied_at,
        "last_status_at": row.last_status_at,
        "notes": row.notes,
        "deleted_at": row.deleted_at,
    }
    if with_logs:
        data["logs"] = [
            {
                "id": log.id,
                "from_status": log.from_status,
                "to_status": log.to_status,
                "changed_at": log.changed_at,
                "note": log.note,
            }
            for log in sorted(row.logs, key=lambda item: (item.changed_at, item.id))
        ]
    return data


def get_app(db: Session, app_id: int) -> Application:
    row = db.get(Application, app_id)
    if row is None:
        raise HTTPException(404, "记录不存在")
    return row


def check_choice(job_type: str, channel: str) -> None:
    if job_type not in JOB_TYPES:
        raise HTTPException(422, "请选择实习或校招")
    if channel not in CHANNELS:
        raise HTTPException(422, "渠道不正确")


@router.get("")
def list_apps(
    page: int = 1,
    status: str | None = None,
    job_type: str | None = None,
    channel: str | None = None,
    q: str | None = None,
    deleted: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    query = db.query(Application)
    if deleted:
        query = query.filter(Application.deleted_at.is_not(None))
    else:
        query = query.filter(Application.deleted_at.is_(None))
    if status:
        query = query.filter(Application.status == status)
    if job_type:
        query = query.filter(Application.job_type == job_type)
    if channel:
        query = query.filter(Application.channel == channel)
    if q and q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(Application.company_name.like(like), Application.position_name.like(like)))
    query = query.order_by(Application.last_status_at.desc(), Application.id.desc())
    total = query.count()
    rows = query.offset(max(page - 1, 0) * PAGE_SIZE).limit(PAGE_SIZE).all()
    return {"items": [dump(row) for row in rows], "total": total, "page": page, "page_size": PAGE_SIZE}


@router.post("")
def create_app(body: AppIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    company = blank(body.company_name)
    position = blank(body.position_name)
    if not company or not position:
        raise HTTPException(422, "请填写公司和岗位")
    check_choice(body.job_type, body.channel)
    now = clock()
    applied = naive(body.applied_at) if body.applied_at else None
    if applied is None:
        if body.status != "communicated":
            raise HTTPException(422, "请填写投递日")
        applied = datetime(now.year, now.month, now.day)
    status_at = naive(body.status_at) if body.status_at else None
    if body.status != "communicated" and status_at is None:
        status_at = now
    try:
        log = initial_log(body.status, applied, status_at, now)
    except RuleError as err:
        fail(err)
    row = Application(
        company_name=company,
        position_name=position,
        job_type=body.job_type,
        channel=body.channel,
        city=blank(body.city),
        salary_range=blank(body.salary_range),
        jd_text=blank(body.jd_text),
        notes=blank(body.notes),
        status=body.status,
        applied_at=applied,
        last_status_at=log.changed_at,
    )
    db.add(row)
    db.flush()
    db.add(StatusLog(application_id=row.id, from_status=None, to_status=log.to_status, changed_at=log.changed_at))
    db.commit()
    db.refresh(row)
    return dump(row, with_logs=True)


@router.get("/{app_id}")
def detail(app_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    return dump(get_app(db, app_id), with_logs=True)


@router.patch("/{app_id}")
def update_app(app_id: int, body: AppPatch, db: Session = Depends(get_db), _: User = Depends(current_user)):
    row = get_app(db, app_id)
    data = body.model_dump(exclude_unset=True)
    if "job_type" in data or "channel" in data:
        check_choice(data.get("job_type", row.job_type), data.get("channel", row.channel))
    for field in ("company_name", "position_name"):
        if field in data:
            value = blank(data[field])
            if not value:
                raise HTTPException(422, "请填写公司和岗位")
            setattr(row, field, value)
    for field in ("job_type", "channel", "city", "salary_range", "jd_text", "notes"):
        if field in data and field not in ("company_name", "position_name"):
            value = data[field]
            setattr(row, field, blank(value) if isinstance(value, str) else value)
    if "applied_at" in data and data["applied_at"] is not None:
        new_applied = naive(data["applied_at"])
        logs = (
            db.query(StatusLog)
            .filter(StatusLog.application_id == row.id)
            .order_by(StatusLog.changed_at, StatusLog.id)
            .all()
        )
        try:
            edited = edit_applied_at(
                row.applied_at,
                new_applied,
                [Log(item.from_status, item.to_status, item.changed_at) for item in logs],
                clock(),
            )
        except RuleError as err:
            fail(err)
        row.applied_at = new_applied
        if edited.move_first_log_to is not None:
            logs[0].changed_at = edited.move_first_log_to
            if edited.update_last_status_at:
                row.last_status_at = edited.move_first_log_to
    db.commit()
    db.refresh(row)
    return dump(row, with_logs=True)


@router.post("/{app_id}/status")
def change_status(app_id: int, body: StatusIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    row = get_app(db, app_id)
    now = clock()
    changed = naive(body.changed_at) if body.changed_at else now
    try:
        check_transition(row.status, body.to_status)
        check_changed_at(changed, row.last_status_at, now)
    except RuleError as err:
        fail(err)
    previous = row.status
    row.status = body.to_status
    row.last_status_at = changed
    db.add(
        StatusLog(
            application_id=row.id,
            from_status=previous,
            to_status=body.to_status,
            changed_at=changed,
            note=blank(body.note),
        )
    )
    db.commit()
    db.refresh(row)
    return dump(row, with_logs=True)


@router.delete("/{app_id}")
def soft_delete(app_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    row = get_app(db, app_id)
    row.deleted_at = clock()
    db.commit()
    return {"ok": True}


@router.post("/{app_id}/restore")
def restore(app_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    row = get_app(db, app_id)
    row.deleted_at = None
    db.commit()
    return dump(row, with_logs=True)
