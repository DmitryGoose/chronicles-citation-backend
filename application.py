from datetime import datetime

import psycopg2

from fastapi import FastAPI, Request, Query, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from database.connection import SessionLocal, DATABASE_URL
from models.chronicle import Chronicle
from models.like import Like
from models.user import User

DEFAULT_IMAGE_URL = "http://localhost:9000/media/laurentian.jpg"

DEFAULT_VIDEO_URL = "ВСТАВЬ_СЮДА_РАБОЧУЮ_ССЫЛКУ_НА_MP4"

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(directory="templates")


# =========================
# GET: Добавление источника
# =========================

@app.get("/add-chronicle")
def add_chronicle(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="add_chronicle.html",
        context={}
    )


# =========================
# GET: Каталог источников
# =========================

@app.get("/chronicle-catalog")
def chronicles_list(
    request: Request,
    year: str | None = None
):
    db: Session = SessionLocal()

    try:
        query = (
            db.query(Chronicle)
            .filter(Chronicle.статус == "опубликован")
        )

        if year:
            year_number = int(year[:4])

            query = query.filter(
                Chronicle.год_начала == year_number
            )

        filtered_chronicles = query.all()

        for chronicle in filtered_chronicles:
            chronicle.likes_count = (
                db.query(Like)
                .filter(
                    Like.услуга_id == chronicle.id
                )
                .count()
            )

        return templates.TemplateResponse(
            request=request,
            name="chronicle_catalog.html",
            context={
                "chronicles": filtered_chronicles,
                "selected_year": year,
            }
        )

    finally:
        db.close()


# =========================
# GET: Лента
# =========================

@app.get("/chronicle-feed/{chronicle_id}")
def feed(
    request: Request,
    chronicle_id: int,
    show_next: bool = Query(False, alias="next")
):
    db: Session = SessionLocal()

    try:
        chronicle = (
            db.query(Chronicle)
            .filter(
                Chronicle.id == chronicle_id,
                Chronicle.статус == "опубликован"
            )
            .first()
        )

        if chronicle is None:
            return {"error": "Источник не найден"}

        # Переход к следующему источнику
        if show_next:
            next_chronicle = (
                db.query(Chronicle)
                .filter(
                    Chronicle.id > chronicle.id,
                    Chronicle.статус == "опубликован"
                )
                .order_by(Chronicle.id)
                .first()
            )

            if next_chronicle:
                chronicle = next_chronicle

        # Предыдущий источник
        previous_chronicle = (
            db.query(Chronicle)
            .filter(
                Chronicle.id < chronicle.id,
                Chronicle.статус == "опубликован"
            )
            .order_by(Chronicle.id.desc())
            .first()
        )

        # Следующий источник
        next_chronicle = (
            db.query(Chronicle)
            .filter(
                Chronicle.id > chronicle.id,
                Chronicle.статус == "опубликован"
            )
            .order_by(Chronicle.id)
            .first()
        )

        # Количество лайков
        likes_count = (
            db.query(Like)
            .filter(
                Like.услуга_id == chronicle.id
            )
            .count()
        )

        return templates.TemplateResponse(
            request=request,
            name="chronicle_feed.html",
            context={
                "chronicle": chronicle,

                "previous_chronicle": previous_chronicle,
                "next_chronicle": next_chronicle,

                "previous_id": (
                    previous_chronicle.id
                    if previous_chronicle
                    else None
                ),

                "next_id": (
                    next_chronicle.id
                    if next_chronicle
                    else None
                ),

                "likes_count": likes_count,
            }
        )

    finally:
        db.close()


# =========================
# POST: Публикация
# ORM
# =========================

@app.post("/publish-chronicle/{chronicle_id}")
def publish_chronicle(chronicle_id: int):
    db: Session = SessionLocal()

    try:
        chronicle = (
            db.query(Chronicle)
            .filter(
                Chronicle.id == chronicle_id
            )
            .first()
        )

        if chronicle is None:
            return {"error": "Источник не найден"}

        if chronicle.статус != "черновик":
            return {
                "error": "Можно публиковать только черновик"
            }

        chronicle.статус = "опубликован"

        db.commit()

        return RedirectResponse(
            url="/chronicle-catalog",
            status_code=303
        )

    finally:
        db.close()


# =========================
# POST: Логическое удаление
# SQL UPDATE + курсор
# =========================

@app.post("/delete-chronicle/{chronicle_id}")
def delete_chronicle(chronicle_id: int):
    connection = psycopg2.connect(DATABASE_URL)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE chronicles
            SET статус = 'удален'
            WHERE id = %s
            """,
            (chronicle_id,)
        )

        connection.commit()

        cursor.close()

        return RedirectResponse(
            url="/chronicle-catalog",
            status_code=303
        )

    finally:
        connection.close()


# =========================
# POST: Добавление
# ORM
# =========================

@app.post("/add-chronicle")
def create_chronicle(
    название: str = Form(...),
    заголовок: str = Form(...),
    описание: str = Form(...),
    год_авторства: int = Form(...),
    год_начала: int = Form(...),

    url_изображения: str | None = Form(None),
    url_видео: str | None = Form(None),
):
    db: Session = SessionLocal()

    try:
        chronicle = Chronicle(
            название=название,
            заголовок=заголовок,
            описание=описание,

            год_авторства=год_авторства,
            год_начала=год_начала,

            url_изображения=url_изображения or DEFAULT_IMAGE_URL,
            url_видео=url_видео or DEFAULT_VIDEO_URL,

            статус="черновик",
            создатель=1,

            дата_создания=datetime.now(),
        )

        db.add(chronicle)

        db.commit()

        return RedirectResponse(
            url="/chronicle-catalog",
            status_code=303
        )

    finally:
        db.close()
