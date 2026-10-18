import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.schemas import MessageResponse, StubAuthRequest, UserRegistrationRequest, UserResponse
from database.connection import get_db
from models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegistrationRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first(): raise HTTPException(status_code=409, detail="Имя пользователя уже занято")
    password_hash = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()
    user=User(username=payload.username, password_hash=password_hash); db.add(user); db.commit(); db.refresh(user); return user

@router.post("/authenticate", response_model=MessageResponse)
def authenticate(_: StubAuthRequest): return MessageResponse(message="Заглушка аутентификации для лабораторной работы 4")

@router.post("/logout", response_model=MessageResponse)
def logout(): return MessageResponse(message="Заглушка деавторизации для лабораторной работы 4")
