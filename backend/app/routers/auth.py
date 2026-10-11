from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import check_password, create_token
from app.db import get_db
from app.models import User

router = APIRouter(prefix="/auth")


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).one_or_none()
    if user is None or not check_password(user, body.password):
        raise HTTPException(401, "用户名或密码错误")
    return {"access_token": create_token(user.id)}
