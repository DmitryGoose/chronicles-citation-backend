from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from controllers.chronicle_controller import router as chronicle_router

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Летописные источники")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/media", StaticFiles(directory=BASE_DIR / "media"), name="media")
app.include_router(chronicle_router)
