from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.models import Application, StatusLog, User

router = APIRouter(prefix="/stats")


def week_start(day: datetime) -> datetime:
    monday = day.date() - timedelta(days=day.weekday())
    return datetime(monday.year, monday.month, monday.day)


@router.get("")
def stats(job_type: str | None = None, db: Session = Depends(get_db), _: User = Depends(current_user)):
    apps = db.query(Application).filter(Application.deleted_at.is_(None))
    if job_type:
        apps = apps.filter(Application.job_type == job_type)
    total = apps.count()

    def reached(status: str) -> int:
        query = (
            db.query(func.count(func.distinct(StatusLog.application_id)))
            .join(Application, Application.id == StatusLog.application_id)
            .filter(Application.deleted_at.is_(None), StatusLog.to_status == status)
        )
        if job_type:
            query = query.filter(Application.job_type == job_type)
        return query.scalar() or 0

    applied_rows = apps.with_entities(Application.applied_at).all()
    trend = []
    if applied_rows:
        start = week_start(min(row.applied_at for row in applied_rows))
        end = week_start(datetime.now())
        counts: dict[datetime, int] = {}
        for row in applied_rows:
            key = week_start(row.applied_at)
            counts[key] = counts.get(key, 0) + 1
        cursor = start
        while cursor <= end:
            trend.append({"week": cursor.date().isoformat(), "count": counts.get(cursor, 0)})
            cursor += timedelta(days=7)

    offer_rows = (
        db.query(Application.applied_at, func.min(StatusLog.changed_at))
        .join(StatusLog, StatusLog.application_id == Application.id)
        .filter(Application.deleted_at.is_(None), StatusLog.to_status == "offered")
    )
    if job_type:
        offer_rows = offer_rows.filter(Application.job_type == job_type)
    spans = []
    for applied_at, offered_at in offer_rows.group_by(Application.id).all():
        spans.append((offered_at - applied_at).total_seconds() / 86400)
    average_days = None
    if spans:
        mean = sum(spans) / len(spans)
        average_days = int(Decimal(str(mean)).quantize(Decimal(1), rounding=ROUND_HALF_UP))

    return {
        "total": total,
        "resume_requested": reached("resume_requested"),
        "interview": reached("interview"),
        "offered": reached("offered"),
        "rejected": apps.filter(Application.status == "rejected").count(),
        "withdrawn": apps.filter(Application.status == "withdrawn").count(),
        "trend": trend,
        "average_days": average_days,
    }
