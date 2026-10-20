import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, Security, status
from sqlalchemy.orm import Session

from api.dependencies import session_cookie
from api.schemas import (
    AuthenticationResponse,
    MessageResponse,
    UserAuthenticationRequest,
    UserRegistrationRequest,
    UserResponse,
)
from api.session import (
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SECURE,
    SESSION_TTL_SECONDS,
    create_session,
    delete_session,
    get_session_user_id,
)
from database.connection import get_db
from models.user import User

router = APIRouter(prefix="/api/users", tags=["Пользователи"])

PASSWORD_ITERATIONS = 210_000


def _password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("ascii"),
            int(iterations),
        ).hex()
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(expected, actual)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать пользователя",
    description="Создаёт пользователя и сохраняет хеш пароля. Сессию не создаёт.",
    responses={409: {"description": "Имя пользователя уже занято"}},
)
def register(payload: UserRegistrationRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Имя пользователя уже занято")
    user = User(username=payload.username, password_hash=_password_hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/authenticate",
    response_model=AuthenticationResponse,
    summary="Аутентифицировать пользователя",
    description=(
        "Проверяет имя и пароль, создаёт сессию в Redis и устанавливает "
        f"HttpOnly cookie `{SESSION_COOKIE_NAME}`."
    ),
    responses={401: {"description": "Неверное имя пользователя или пароль"}},
)
def authenticate(
    payload: UserAuthenticationRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )

    session_id = create_session(user.id, user.username)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return AuthenticationResponse(
        id=user.id,
        username=user.username,
        message="Аутентификация выполнена",
        expires_in=SESSION_TTL_SECONDS,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Завершить сессию",
    description="Удаляет текущую сессию из Redis и очищает cookie браузера.",
    responses={401: {"description": "Требуется аутентификация"}},
)
def logout(
    response: Response,
    session_id: str | None = Security(session_cookie),
):
    if not session_id or get_session_user_id(session_id) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
        )
    delete_session(session_id)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return MessageResponse(message="Сессия завершена")
