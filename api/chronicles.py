from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user_id
from api.schemas import ChronicleDraft, ChronicleFeedItem, ChronicleListItem, LikeRequest, PublishChronicleRequest
from api.storage import ALLOWED_IMAGE_TYPES, ALLOWED_VIDEO_TYPES, media_url, upload_media
from database.connection import get_db
from models.chronicle import Chronicle
from models.like import Like

router = APIRouter(prefix="/api/chronicles", tags=["Летописные источники"])
DEFAULT_IMAGE_URL = "/media/chronicle_default.jpg"
DEFAULT_VIDEO_URL = "/media/chronicle_default.mp4"


def _published(db: Session):
    return db.query(Chronicle).filter(Chronicle.status == "опубликован")


def _list_item(item: Chronicle, current_user_id: int | None = None) -> ChronicleListItem:
    return ChronicleListItem(
        id=item.id,
        name=item.name,
        short_description=item.short_description,
        authorship_year=item.authorship_year,
        start_year=item.start_year,
        image_url=media_url(item.image_url, DEFAULT_IMAGE_URL),
        video_url=media_url(item.video_url, DEFAULT_VIDEO_URL),
        is_owner=int(current_user_id is not None and item.creator_id == current_user_id),
    )


@router.get(
    "",
    response_model=list[ChronicleListItem],
    summary="Получить список источников",
    description="Публичный метод. Возвращает опубликованные источники с необязательной фильтрацией по году.",
)
def list_chronicles(
    start_year: int | None = Query(None, ge=1, le=2100),
    db: Session = Depends(get_db),
):
    query = _published(db)
    if start_year is not None:
        query = query.filter(Chronicle.start_year == start_year)
    return [_list_item(item) for item in query.order_by(Chronicle.id).all()]


@router.post(
    "",
    response_model=ChronicleDraft,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить источник",
    description="Защищённый метод. Создаёт черновик текущего пользователя и загружает файлы в MinIO.",
    responses={401: {"description": "Требуется аутентификация"}, 409: {"description": "Черновик уже существует"}},
)
async def create_draft(
    name: str = Form(..., min_length=1, max_length=255),
    image: UploadFile = File(...),
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    if db.query(Chronicle).filter(Chronicle.creator_id == current_user_id, Chronicle.status == "черновик").first():
        raise HTTPException(status_code=409, detail="У пользователя уже есть черновик")
    image_name = await upload_media(image, ALLOWED_IMAGE_TYPES)
    video_name = await upload_media(video, ALLOWED_VIDEO_TYPES)
    item = Chronicle(
        name=name.strip(),
        status="черновик",
        image_url=image_name,
        video_url=video_name,
        created_at=datetime.now(),
        creator_id=current_user_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return ChronicleDraft(
        id=item.id,
        name=item.name,
        short_description=None,
        authorship_year=None,
        start_year=None,
        image_url=media_url(item.image_url, DEFAULT_IMAGE_URL),
        video_url=media_url(item.video_url, DEFAULT_VIDEO_URL),
        created_at=item.created_at,
    )


@router.get(
    "/draft",
    response_model=ChronicleDraft,
    summary="Получить черновик",
    description="Защищённый метод. Возвращает единственный черновик текущего пользователя.",
    responses={401: {"description": "Требуется аутентификация"}, 404: {"description": "Черновик не найден"}},
)
def get_draft(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    item = db.query(Chronicle).filter(Chronicle.creator_id == current_user_id, Chronicle.status == "черновик").first()
    if item is None:
        raise HTTPException(status_code=404, detail="Черновик не найден")
    return ChronicleDraft(
        id=item.id,
        name=item.name,
        short_description=item.short_description,
        authorship_year=item.authorship_year,
        start_year=item.start_year,
        image_url=media_url(item.image_url, DEFAULT_IMAGE_URL),
        video_url=media_url(item.video_url, DEFAULT_VIDEO_URL),
        created_at=item.created_at,
    )


@router.put(
    "/{chronicle_id}/publish",
    response_model=ChronicleListItem,
    summary="Опубликовать источник",
    description="Защищённый метод. Публикует только черновик текущего пользователя.",
    responses={401: {"description": "Требуется аутентификация"}, 404: {"description": "Черновик пользователя не найден"}},
)
def publish_chronicle(
    chronicle_id: int,
    payload: PublishChronicleRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    item = db.query(Chronicle).filter(
        Chronicle.id == chronicle_id,
        Chronicle.creator_id == current_user_id,
        Chronicle.status == "черновик",
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Черновик пользователя не найден")
    item.short_description = payload.short_description.strip()
    item.authorship_year = payload.authorship_year
    item.start_year = payload.start_year
    item.status = "опубликован"
    item.published_at = datetime.now()
    db.commit()
    db.refresh(item)
    return _list_item(item, current_user_id)


@router.get(
    "/feed",
    response_model=ChronicleFeedItem,
    summary="Получить запись ленты",
    description="Публичный метод. Возвращает первую, указанную или следующую опубликованную запись.",
)
def get_feed(
    chronicle_id: int | None = None,
    show_next: bool = Query(False, alias="next"),
    db: Session = Depends(get_db),
):
    items = _published(db).order_by(Chronicle.id).all()
    if not items:
        raise HTTPException(status_code=404, detail="Опубликованные источники не найдены")
    index = 0
    if chronicle_id is not None:
        index = builtins_next((i for i, item in enumerate(items) if item.id == chronicle_id), -1)
        if index < 0:
            raise HTTPException(status_code=404, detail="Источник не найден")
    if show_next:
        index = (index + 1) % len(items)
    item = items[index]
    return ChronicleFeedItem(
        **_list_item(item).model_dump(),
        likes_count=db.query(Like).filter(Like.chronicle_id == item.id).count(),
        is_liked=0,
    )


@router.post(
    "/{chronicle_id}/like",
    response_model=ChronicleFeedItem,
    summary="Изменить лайк",
    description="Защищённый метод. Значение 1 ставит лайк, 0 снимает лайк текущего пользователя.",
    responses={401: {"description": "Требуется аутентификация"}, 404: {"description": "Источник не найден"}},
)
def set_like(
    chronicle_id: int,
    payload: LikeRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    item = _published(db).filter(Chronicle.id == chronicle_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Источник не найден")
    existing = db.query(Like).filter(Like.user_id == current_user_id, Like.chronicle_id == chronicle_id).first()
    if payload.value == 1 and existing is None:
        db.add(Like(user_id=current_user_id, chronicle_id=chronicle_id))
    if payload.value == 0 and existing is not None:
        db.delete(existing)
    db.commit()
    return ChronicleFeedItem(
        **_list_item(item, current_user_id).model_dump(),
        likes_count=db.query(Like).filter(Like.chronicle_id == chronicle_id).count(),
        is_liked=payload.value,
    )


@router.delete(
    "/{chronicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить источник",
    description="Защищённый метод. Логически удаляет только источник текущего пользователя.",
    responses={401: {"description": "Требуется аутентификация"}, 404: {"description": "Источник пользователя не найден"}},
)
def delete_chronicle(
    chronicle_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    item = db.query(Chronicle).filter(
        Chronicle.id == chronicle_id,
        Chronicle.creator_id == current_user_id,
        Chronicle.status != "удален",
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Источник пользователя не найден")
    item.status = "удален"
    db.commit()


builtins_next = next
