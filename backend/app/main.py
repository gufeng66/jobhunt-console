from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

app = FastAPI()
api = APIRouter(prefix="/api")


@api.get("/health")
def health(db: Session = Depends(get_db)):
    now = db.execute(text("SELECT NOW()")).scalar()
    return {"now": now.isoformat(sep=" ") if now else None}


app.include_router(api)
