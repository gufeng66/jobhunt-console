import bcrypt
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User


def upsert_user(db: Session) -> None:
    password = settings.initial_password.encode()
    user = db.query(User).filter(User.username == settings.username).one_or_none()
    if user is None:
        db.add(User(username=settings.username, password_hash=bcrypt.hashpw(password, bcrypt.gensalt()).decode()))
    elif not bcrypt.checkpw(password, user.password_hash.encode()):
        user.password_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
    db.commit()
