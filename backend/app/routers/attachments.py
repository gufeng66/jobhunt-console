import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import settings
from app.db import get_db
from app.models import Application, Attachment, User

router = APIRouter(prefix="/applications/{app_id}/attachments")
MAX_BYTES = 10 * 1024 * 1024
TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def live_app(db: Session, app_id: int) -> Application:
    row = db.get(Application, app_id)
    if row is None or row.deleted_at is not None:
        raise HTTPException(404, "记录不存在")
    return row


@router.get("")
def list_files(app_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    live_app(db, app_id)
    rows = db.query(Attachment).filter(Attachment.application_id == app_id).order_by(Attachment.id).all()
    return [
        {
            "id": row.id,
            "filename": row.filename,
            "size": row.size,
            "content_type": row.content_type,
            "uploaded_at": row.uploaded_at,
        }
        for row in rows
    ]


@router.post("")
async def upload(app_id: int, file: UploadFile, db: Session = Depends(get_db), _: User = Depends(current_user)):
    live_app(db, app_id)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in TYPES:
        raise HTTPException(422, "只接受 pdf 或 docx")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(422, "文件不能超过 10MB")
    relative = f"{app_id}/{uuid.uuid4().hex}{ext}"
    path = Path(settings.upload_dir) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    row = Attachment(
        application_id=app_id,
        filename=Path(file.filename or "").name,
        stored_path=relative,
        size=len(data),
        content_type=TYPES[ext],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "filename": row.filename, "size": row.size, "content_type": row.content_type}


@router.get("/{file_id}")
def download(app_id: int, file_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    live_app(db, app_id)
    row = db.get(Attachment, file_id)
    if row is None or row.application_id != app_id:
        raise HTTPException(404, "附件不存在")
    path = Path(settings.upload_dir) / row.stored_path
    if not path.is_file():
        raise HTTPException(404, "附件不存在")
    return FileResponse(path, filename=row.filename, media_type=row.content_type)


@router.delete("/{file_id}")
def remove(app_id: int, file_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    live_app(db, app_id)
    row = db.get(Attachment, file_id)
    if row is None or row.application_id != app_id:
        raise HTTPException(404, "附件不存在")
    path = Path(settings.upload_dir) / row.stored_path
    if path.is_file():
        path.unlink()
    db.delete(row)
    db.commit()
    return {"ok": True}
