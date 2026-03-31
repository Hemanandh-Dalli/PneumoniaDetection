from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from routes.auth import router as auth_router
from routes.chat import router as chat_router
from routes.history import router as history_router
from routes.predict import router as predict_router
from routes.report import router as report_router
from utils.config import UPLOAD_DIR, get_allowed_origins
from database.db import Base, engine
from database import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Pneumonia Detection API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(chat_router)
app.include_router(report_router)
app.include_router(auth_router)
app.include_router(history_router)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/health")
def health_check():
    return {"status": "ok"}
