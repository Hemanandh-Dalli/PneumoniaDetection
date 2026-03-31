import io
import json
import mimetypes
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import requests
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google import genai
from google.genai import types as genai_types
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from supabase import Client, create_client


JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
CLASS_LABELS = [
    "Covid-19",
    "Normal",
    "Pneumonia-Bacterial",
    "Pneumonia-Viral",
]
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)
app = FastAPI(title="Pneumonia Detection API")


def get_allowed_origins() -> list[str]:
    raw_value = (os.getenv("ALLOWED_ORIGINS") or "").strip()
    if not raw_value:
        return DEFAULT_ALLOWED_ORIGINS.copy()
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    email: str
    password: str


class ChatRequest(BaseModel):
    chat_id: int
    message: str


class ReportRequest(BaseModel):
    predicted_class: str
    confidence: float
    explanation: str
    image_path: str
    heatmap_path: str = ""


def require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"{name} is missing")
    return value


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    return create_client(
        require_env("SUPABASE_URL"),
        require_env("SUPABASE_SERVICE_ROLE_KEY"),
    )


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    return genai.Client(api_key=require_env("GEMINI_API_KEY"))


def get_gemini_model() -> str:
    return (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()


def get_bucket_name() -> str:
    return (os.getenv("SUPABASE_BUCKET") or "xrays").strip()


def get_secret_key() -> str:
    return require_env("SECRET_KEY")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


def create_access_token(email: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": email,
        "exp": expires_at,
    }
    return jwt.encode(payload, get_secret_key(), algorithm=JWT_ALGORITHM)


def get_user_by_email(email: str):
    response = (
        get_supabase()
        .table("users")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    return (response.data or [None])[0]


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = jwt.decode(
            credentials.credentials,
            get_secret_key(),
            algorithms=[JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def parse_gemini_json(raw_text: str) -> dict:
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Empty Gemini response")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def clamp_confidence(value) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.5


def assess_xray(image_bytes: bytes, mime_type: str) -> tuple[str, float, str]:
    prompt = f"""
You are assisting with chest X-ray screening triage for an educational web app.

Classify the uploaded image into exactly one of these labels:
- Covid-19
- Normal
- Pneumonia-Bacterial
- Pneumonia-Viral

Return strict JSON with this shape:
{{
  "predicted_class": "<one label from the list>",
  "confidence": <number from 0 to 1>,
  "explanation": "<4 to 6 concise sentences in simple language. Mention this is an AI screening result and not a diagnosis. No treatment instructions.>"
}}
"""

    response = get_gemini_client().models.generate_content(
        model=get_gemini_model(),
        contents=[
            prompt,
            genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
    )
    payload = parse_gemini_json(response.text)

    predicted_class = payload.get("predicted_class")
    if predicted_class not in CLASS_LABELS:
        predicted_class = "Normal"

    confidence = clamp_confidence(payload.get("confidence"))
    explanation = (payload.get("explanation") or "").strip()
    if not explanation:
        explanation = (
            "This AI screening result should be reviewed with clinical context. "
            "It is not a confirmed diagnosis."
        )

    return predicted_class, confidence, explanation


def chat_with_gemini(conversation: str) -> str:
    response = get_gemini_client().models.generate_content(
        model=get_gemini_model(),
        contents=f"""
You are a medical follow-up assistant for a pneumonia screening app.

Conversation:
{conversation}

Rules:
- Use simple language
- Maximum 4 lines
- Do not prescribe treatment
- Do not present a final diagnosis
- Suggest clinical follow-up when symptoms are concerning
""",
    )
    text = (response.text or "").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return (
            "I could not generate a follow-up response right now. "
            "Please consult a clinician if symptoms are worsening."
        )
    return "\n".join(lines[:4])


def upload_to_storage(path: str, data: bytes, mime_type: str) -> str:
    bucket = get_bucket_name()
    storage = get_supabase().storage.from_(bucket)
    storage.upload(
        path=path,
        file=data,
        file_options={
            "cache-control": "3600",
            "content-type": mime_type,
            "upsert": "false",
        },
    )
    return storage.get_public_url(path)


def insert_row(table: str, payload: dict) -> dict:
    response = get_supabase().table(table).insert(payload).execute()
    data = response.data or []
    if not data:
        raise RuntimeError(f"Insert failed for table {table}")
    return data[0]


def fetch_rows(table: str, filters: list[tuple[str, str, object]], order_by: str | None = None):
    query = get_supabase().table(table).select("*")
    for field, operator, value in filters:
        if operator == "eq":
            query = query.eq(field, value)
        else:
            raise ValueError(f"Unsupported operator: {operator}")
    if order_by:
        query = query.order(order_by)
    return query.execute().data or []


def load_remote_image(url: str) -> io.BytesIO | None:
    if not url or not url.startswith("http"):
        return None

    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return io.BytesIO(response.content)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/register")
def register(data: RegisterRequest):
    existing = get_user_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    insert_row(
        "users",
        {
            "email": data.email,
            "password_hash": hash_password(data.password),
        },
    )
    return {"message": "User registered successfully"}


@app.post("/api/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = get_user_by_email(username)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {
        "access_token": create_access_token(user["email"]),
        "token_type": "bearer",
    }


@app.post("/api/predict")
async def predict_image(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if len(image_bytes) > 4_000_000:
        raise HTTPException(status_code=413, detail="Image must be under 4 MB for Vercel upload limits")

    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "image/jpeg"
    storage_path = f"{current_user['id']}/{uuid.uuid4()}-{(file.filename or 'xray').replace(' ', '-')}"

    try:
        image_url = upload_to_storage(storage_path, image_bytes, mime_type)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to upload image to Supabase Storage. Verify the bucket exists and service role key is valid.",
        ) from exc

    try:
        predicted_class, confidence, explanation = assess_xray(image_bytes, mime_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    prediction = insert_row(
        "predictions",
        {
            "user_id": current_user["id"],
            "image_path": image_url,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "explanation": explanation,
        },
    )
    chat = insert_row("chats", {"prediction_id": prediction["id"]})
    insert_row(
        "chat_messages",
        {
            "chat_id": chat["id"],
            "role": "assistant",
            "message": explanation,
        },
    )

    return {
        "prediction_id": prediction["id"],
        "chat_id": chat["id"],
        "predicted_class": predicted_class,
        "confidence": confidence,
        "explanation": explanation,
        "image_path": image_url,
        "heatmap_path": "",
    }


@app.get("/api/my-predictions")
def my_predictions(current_user=Depends(get_current_user)):
    predictions = fetch_rows(
        "predictions",
        [("user_id", "eq", current_user["id"])],
        order_by="created_at",
    )
    predictions.reverse()

    chats = fetch_rows("chats", [], order_by="created_at")
    chat_by_prediction = {chat["prediction_id"]: chat for chat in chats}

    return [
        {
            "id": item["id"],
            "predicted_class": item["predicted_class"],
            "confidence": item["confidence"],
            "created_at": item["created_at"],
            "image_path": item["image_path"],
            "chat_id": chat_by_prediction.get(item["id"], {}).get("id"),
        }
        for item in predictions
    ]


@app.get("/api/history")
def history(current_user=Depends(get_current_user)):
    return my_predictions(current_user)


@app.get("/api/chat/{chat_id}")
def get_chat(chat_id: int, current_user=Depends(get_current_user)):
    prediction_rows = fetch_rows("predictions", [("user_id", "eq", current_user["id"])])
    prediction_ids = {row["id"] for row in prediction_rows}
    chat_rows = fetch_rows("chats", [("id", "eq", chat_id)])
    chat = (chat_rows or [None])[0]
    if not chat or chat["prediction_id"] not in prediction_ids:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = fetch_rows("chat_messages", [("chat_id", "eq", chat_id)], order_by="created_at")
    return {
        "chat_id": chat_id,
        "messages": [
            {
                "role": message["role"],
                "message": message["message"],
                "created_at": message["created_at"],
            }
            for message in messages
        ],
    }


@app.post("/api/chat")
def chat(req: ChatRequest, current_user=Depends(get_current_user)):
    prediction_rows = fetch_rows("predictions", [("user_id", "eq", current_user["id"])])
    prediction_ids = {row["id"] for row in prediction_rows}
    chat_rows = fetch_rows("chats", [("id", "eq", req.chat_id)])
    chat_row = (chat_rows or [None])[0]
    if not chat_row or chat_row["prediction_id"] not in prediction_ids:
        raise HTTPException(status_code=400, detail="Invalid chat_id")

    insert_row(
        "chat_messages",
        {
            "chat_id": req.chat_id,
            "role": "user",
            "message": req.message,
        },
    )

    history_rows = fetch_rows("chat_messages", [("chat_id", "eq", req.chat_id)], order_by="created_at")
    conversation = "\n".join(f"{row['role'].upper()}: {row['message']}" for row in history_rows)

    reply = chat_with_gemini(conversation)
    insert_row(
        "chat_messages",
        {
            "chat_id": req.chat_id,
            "role": "ai",
            "message": reply,
        },
    )
    return {"reply": reply}


@app.post("/api/report")
def generate_report(data: ReportRequest, current_user=Depends(get_current_user)):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Pneumonia Detection Report</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    table_data = [
        ["Assessment", data.predicted_class],
        ["Confidence", f"{data.confidence * 100:.2f}%"],
    ]
    table = Table(table_data, colWidths=[150, 250])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>Explanation:</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(data.explanation.replace("\n", "<br/>"), styles["Normal"]))
    elements.append(Spacer(1, 20))

    image_stream = load_remote_image(data.image_path)
    if image_stream:
        elements.append(Paragraph("<b>Uploaded X-ray:</b>", styles["Heading2"]))
        elements.append(Spacer(1, 10))
        elements.append(Image(image_stream, width=4 * inch, height=4 * inch))
        elements.append(Spacer(1, 20))

    heatmap_stream = load_remote_image(data.heatmap_path)
    if heatmap_stream:
        elements.append(Paragraph("<b>AI Focus Areas:</b>", styles["Heading2"]))
        elements.append(Spacer(1, 10))
        elements.append(Image(heatmap_stream, width=4 * inch, height=4 * inch))
        elements.append(Spacer(1, 20))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=pneumonia_report.pdf"},
    )
