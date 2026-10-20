import json
import os
import uuid
from functools import lru_cache

from fastapi import HTTPException, status
from redis import Redis
from redis.exceptions import RedisError

SESSION_COOKIE_NAME = "chronicles_session"
SESSION_KEY_PREFIX = "session:"
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")


@lru_cache(maxsize=1)
def get_redis() -> Redis:
    return Redis.from_url(REDIS_URL, decode_responses=True)


def _redis_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Хранилище сессий временно недоступно",
    )


def create_session(user_id: int, username: str) -> str:
    session_id = uuid.uuid4().hex
    try:
        get_redis().setex(
            f"{SESSION_KEY_PREFIX}{session_id}",
            SESSION_TTL_SECONDS,
            json.dumps({"user_id": user_id, "username": username}, ensure_ascii=False),
        )
    except RedisError as exc:
        raise _redis_error() from exc
    return session_id


def get_session_user_id(session_id: str) -> int | None:
    try:
        value = get_redis().get(f"{SESSION_KEY_PREFIX}{session_id}")
    except RedisError as exc:
        raise _redis_error() from exc
    if value is None:
        return None
    try:
        return int(json.loads(value)["user_id"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def delete_session(session_id: str) -> None:
    try:
        get_redis().delete(f"{SESSION_KEY_PREFIX}{session_id}")
    except RedisError as exc:
        raise _redis_error() from exc
