from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyCookie

from api.session import SESSION_COOKIE_NAME, get_session_user_id

session_cookie = APIKeyCookie(
    name=SESSION_COOKIE_NAME,
    scheme_name="CookieSession",
    description="Cookie с идентификатором сессии, которую устанавливает POST /api/users/authenticate.",
    auto_error=False,
)


def get_current_user_id(
    session_id: str | None = Security(session_cookie),
) -> int:
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
        )

    user_id = get_session_user_id(session_id)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия отсутствует или истекла",
        )
    return user_id
