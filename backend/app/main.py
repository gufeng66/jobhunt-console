from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
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


app.include_router(api)
