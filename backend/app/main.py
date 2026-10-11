from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
from app.routers import applications, attachments, auth, stats
from app.users import upsert_user


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db = SessionLocal()
    try:
        upsert_user(db)
    finally:
        db.close()
    yield


app = FastAPI(lifespan=lifespan)
api = APIRouter(prefix="/api")


@api.get("/health")
def health(db: Session = Depends(get_db)):
    now = db.execute(text("SELECT NOW()")).scalar()
    return {"now": now.isoformat(sep=" ") if now else None}


api.include_router(auth.router)
api.include_router(applications.router)
api.include_router(attachments.router)
api.include_router(stats.router)
app.include_router(api)
