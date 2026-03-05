from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.predict import router as predict_router
from routes.chat import router as chat_router
from routes.report import router as report_router
from fastapi.staticfiles import StaticFiles

from routes.auth import router as auth_router
from routes.history import router as history_router


app = FastAPI(title="Pneumonia Detection API")

# ✅ CORS FIX (THIS IS THE IMPORTANT PART)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(chat_router)
app.include_router(report_router)
app.include_router(auth_router)
app.include_router(history_router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")