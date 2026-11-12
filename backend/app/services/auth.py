import base64
import hashlib
import os
from datetime import datetime, timedelta
from typing import Any

import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    password_digest = hashlib.sha256(password.encode('utf-8')).digest()
    return bcrypt.hashpw(password_digest, bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        if stored_hash.startswith(("$2a$", "$2b$", "$2y$")):
            password_digest = hashlib.sha256(password.encode('utf-8')).digest()
            return bcrypt.checkpw(password_digest, stored_hash.encode('utf-8'))

        raw = base64.b64decode(stored_hash.encode('utf-8'))
        salt, derived = raw[:16], raw[16:]
        candidate = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
        return candidate == derived
    except Exception:
        return False


def create_access_token(subject: str | int) -> str:
    payload = {
        'sub': str(subject),
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow(),
    }
    return jwt.encode(payload, settings.secret_key, algorithm='HS256')


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=['HS256'])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token') from exc


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token payload')

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user


def get_current_user(current_user: User | None = Depends(get_optional_current_user)) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')
    return current_user
