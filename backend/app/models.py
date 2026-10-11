from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Application(Base):
    __tablename__ = "application"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(128))
    position_name: Mapped[str] = mapped_column(String(128))
    job_type: Mapped[str] = mapped_column(String(16))
    channel: Mapped[str] = mapped_column(String(16))
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(64), nullable=True)
    jd_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    applied_at: Mapped[datetime] = mapped_column(DateTime)
    last_status_at: Mapped[datetime] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    logs: Mapped[list["StatusLog"]] = relationship(order_by="StatusLog.changed_at, StatusLog.id")
    attachments: Mapped[list["Attachment"]] = relationship()


class StatusLog(Base):
    __tablename__ = "application_status_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("application.id"))
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32))
    changed_at: Mapped[datetime] = mapped_column(DateTime)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Attachment(Base):
    __tablename__ = "attachment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("application.id"))
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(128))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
