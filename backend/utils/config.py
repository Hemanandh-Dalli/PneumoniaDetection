import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_DIR = BASE_DIR / "reports"
MODEL_PATH = BASE_DIR / "model" / "pneumonia.keras"

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]


def get_allowed_origins() -> list[str]:
    raw_value = (os.getenv("ALLOWED_ORIGINS") or "").strip()
    if not raw_value:
        return DEFAULT_ALLOWED_ORIGINS.copy()
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


def to_public_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").lstrip("/")


def public_to_filesystem_path(path: str | Path) -> Path:
    candidate = (BASE_DIR / str(path).lstrip("/")).resolve()
    if BASE_DIR.resolve() not in candidate.parents and candidate != BASE_DIR.resolve():
        raise ValueError("Path resolves outside backend directory")
    return candidate
