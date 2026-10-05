from datetime import datetime
from pathlib import Path

import psycopg2
from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.connection import DATABASE_URL, SessionLocal
from models.chronicle import Chronicle
from models.like import Like

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter(prefix="/chronicles", tags=["Летописи"])

CURRENT_USER_ID = 1
DEFAULT_IMAGE_URL = "/media/chronicle_default.jpg"
DEFAULT_VIDEO_URL = "/media/chronicle_default.mp4"
INVALID_IMAGE_URL = "http://localhost:9000/chronicles/pending-image.jpg"
INVALID_VIDEO_URL = "http://localhost:9000/chronicles/pending-video.mp4"


def _published_query(db: Session):
    return db.query(Chronicle).filter(Chronicle.status == "опубликован")


# GET 1 из 3: лента одной опубликованной летописи.
@router.get("/feed")
def get_chronicle_feed(
    request: Request,
    chronicle_id: int | None = Query(None),
    show_next: bool = Query(False, alias="next"),
):
    db: Session = SessionLocal()
    try:
        first_chronicle = _published_query(db).order_by(Chronicle.id).first()
        if first_chronicle is None:
            raise HTTPException(status_code=404, detail="Опубликованные летописи не найдены")

        if chronicle_id is None:
            chronicle = first_chronicle
        else:
            chronicle = _published_query(db).filter(Chronicle.id == chronicle_id).first()
            if chronicle is None:
                raise HTTPException(status_code=404, detail="Летопись не найдена")

        if show_next:
            chronicle = (
                _published_query(db)
                .filter(Chronicle.id > chronicle.id)
                .order_by(Chronicle.id)
                .first()
                or first_chronicle
            )

        likes_count = db.query(Like).filter(Like.chronicle_id == chronicle.id).count()
        return templates.TemplateResponse(
            request=request,
            name="chronicle_feed.html",
            context={
                "chronicle": chronicle,
                "likes_count": likes_count,
                "default_image_url": DEFAULT_IMAGE_URL,
                "default_video_url": DEFAULT_VIDEO_URL,
            },
        )
    finally:
        db.close()


# GET 2 из 3: черновик пользователя или первый шаг добавления.
@router.get("/add")
def get_chronicle_draft(request: Request):
    db: Session = SessionLocal()
    try:
        draft = (
            db.query(Chronicle)
            .filter(
                Chronicle.creator_id == CURRENT_USER_ID,
                Chronicle.status == "черновик",
            )
            .first()
        )
        return templates.TemplateResponse(
            request=request,
            name="chronicle_add.html",
            context={
                "draft": draft,
                "default_image_url": DEFAULT_IMAGE_URL,
                "default_video_url": DEFAULT_VIDEO_URL,
            },
        )
    finally:
        db.close()


# GET 3 из 3: плитка опубликованных летописей с серверной фильтрацией.
@router.get("/catalog")
def get_chronicle_catalog(
    request: Request,
    start_year: int | None = Query(None, ge=1, le=2100),
):
    db: Session = SessionLocal()
    try:
        likes_subquery = (
            db.query(
                Like.chronicle_id.label("chronicle_id"),
                func.count(Like.id).label("likes_count"),
            )
            .group_by(Like.chronicle_id)
            .subquery()
        )
        query = (
            db.query(
                Chronicle,
                func.coalesce(likes_subquery.c.likes_count, 0).label("likes_count"),
            )
            .outerjoin(likes_subquery, Chronicle.id == likes_subquery.c.chronicle_id)
            .filter(Chronicle.status == "опубликован")
        )
        if start_year is not None:
            query = query.filter(Chronicle.start_year == start_year)

        chronicles = [
            {"item": chronicle, "likes_count": likes_count}
            for chronicle, likes_count in query.order_by(Chronicle.id).all()
        ]
        return templates.TemplateResponse(
            request=request,
            name="chronicle_catalog.html",
            context={
                "chronicles": chronicles,
                "selected_start_year": start_year,
                "default_image_url": DEFAULT_IMAGE_URL,
            },
        )
    finally:
        db.close()


# POST 1 из 3: создание черновика через ORM после кнопки «Далее».
@router.post("")
def create_chronicle_draft(name: str = Form(..., min_length=1, max_length=255)):
    db: Session = SessionLocal()
    try:
        existing_draft = (
            db.query(Chronicle)
            .filter(
                Chronicle.creator_id == CURRENT_USER_ID,
                Chronicle.status == "черновик",
            )
            .first()
        )
        if existing_draft is None:
            db.add(
                Chronicle(
                    name=name.strip(),
                    status="черновик",
                    image_url=INVALID_IMAGE_URL,
                    video_url=INVALID_VIDEO_URL,
                    created_at=datetime.now(),
                    creator_id=CURRENT_USER_ID,
                )
            )
            db.commit()
        return RedirectResponse(url="/chronicles/add", status_code=303)
    finally:
        db.close()


# POST 2 из 3: заполнение и публикация черновика через ORM.
@router.post("/{chronicle_id}/publish")
def publish_chronicle(
    chronicle_id: int,
    short_description: str = Form(..., min_length=1),
    authorship_year: int = Form(..., ge=1, le=2100),
    start_year: int = Form(..., ge=1, le=2100),
):
    db: Session = SessionLocal()
    try:
        chronicle = (
            db.query(Chronicle)
            .filter(
                Chronicle.id == chronicle_id,
                Chronicle.creator_id == CURRENT_USER_ID,
                Chronicle.status == "черновик",
            )
            .first()
        )
        if chronicle is None:
            raise HTTPException(status_code=404, detail="Черновик не найден")

        chronicle.short_description = short_description.strip()
        chronicle.authorship_year = authorship_year
        chronicle.start_year = start_year
        chronicle.status = "опубликован"
        chronicle.published_at = datetime.now()
        db.commit()
        return RedirectResponse(url="/chronicles/catalog", status_code=303)
    finally:
        db.close()


# POST 3 из 3: логическое удаление прямым SQL UPDATE через курсор.
@router.post("/{chronicle_id}/delete")
def delete_chronicle(chronicle_id: int):
    connection = psycopg2.connect(DATABASE_URL)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE chronicles
                SET status = 'удален'
                WHERE id = %s AND status <> 'удален'
                """,
                (chronicle_id,),
            )
        connection.commit()
        return RedirectResponse(url="/chronicles/catalog", status_code=303)
    finally:
        connection.close()
