from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates

from data.collections import chronicles


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/add")
def add_chronicle(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="add.html",
        context={}
    )


@app.get("/chronicles")
def chronicles_list(
    request: Request,
    year: str | None = None
):
    filtered_chronicles = chronicles

    if year:
        year_number = int(year[:4])

        filtered_chronicles = [
            chronicle
            for chronicle in chronicles
            if chronicle["год_начала"] == year_number
        ]

    return templates.TemplateResponse(
        request=request,
        name="chronicles.html",
        context={
            "chronicles": filtered_chronicles,
            "selected_year": year,
        }
    )


@app.get("/feed/{chronicle_id}")
def feed(
    request: Request,
    chronicle_id: int,
    show_next: bool = Query(False, alias="next")
):
    current_index = next(
        (
            index
            for index, item in enumerate(chronicles)
            if item["id"] == chronicle_id
        ),
        None
    )

    if current_index is None:
        return {"error": "Источник не найден"}

    if show_next and current_index < len(chronicles) - 1:
        current_index += 1

    chronicle = chronicles[current_index]

    likes_count = len(chronicle["лайки"])

    previous_chronicle = current_index > 0
    next_chronicle = current_index < len(chronicles) - 1

    previous_id = (
        chronicles[current_index - 1]["id"]
        if previous_chronicle
        else None
    )

    next_id = (
        chronicles[current_index + 1]["id"]
        if next_chronicle
        else None
    )

    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "chronicle": chronicle,
            "previous_chronicle": previous_chronicle,
            "previous_id": previous_id,
            "next_chronicle": next_chronicle,
            "next_id": next_id,
            "likes_count": likes_count,
        }
    )
