from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Report, SavedProduct, SearchHistory, User
from app.services.auth import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(tags=['auth'])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


@router.post('/auth/register', status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    normalized_email = payload.email.lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='An account already exists for this email.')

    user = User(
        name=payload.name.strip(),
        email=normalized_email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='An account already exists for this email.',
        ) from exc
    db.refresh(user)

    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'token': create_access_token(user.id),
    }


@router.post('/auth/login')
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password.')

    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'token': create_access_token(user.id),
    }


@router.get('/auth/me')
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return {
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
    }


@router.get('/profile')
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
        'updated_at': current_user.updated_at.isoformat() if current_user.updated_at else None,
        'saved_product_count': db.query(SavedProduct).filter(SavedProduct.user_id == current_user.id).count(),
        'search_count': db.query(SearchHistory).filter(SearchHistory.user_id == current_user.id).count(),
        'report_count': db.query(Report).filter(Report.user_id == current_user.id).count(),
    }


@router.put('/profile')
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Name cannot be empty.')
        current_user.name = name
    if payload.email is not None:
        email = payload.email.lower()
        existing = db.query(User).filter(User.email == email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='That email address is already in use.')
        current_user.email = email
    db.commit()
    db.refresh(current_user)
    return {'id': current_user.id, 'name': current_user.name, 'email': current_user.email}
