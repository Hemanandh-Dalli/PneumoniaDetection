from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.db import get_db
from database.crud import save_chat_message, get_chat_messages
from database.models import Chat
from services.gemini_service import chat_with_gemini

router = APIRouter()


class ChatRequest(BaseModel):
    chat_id: int
    message: str


# -----------------------------------------
# GET FULL CHAT HISTORY
# -----------------------------------------
@router.get("/chat/{chat_id}")
def get_chat(chat_id: int, db: Session = Depends(get_db)):

    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = get_chat_messages(db, chat_id)

    return {
        "chat_id": chat_id,
        "messages": [
            {
                "role": msg.role,
                "message": msg.message,
                "created_at": msg.created_at,
            }
            for msg in messages
        ],
    }


# -----------------------------------------
# SEND MESSAGE
# -----------------------------------------
@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):

    chat = db.query(Chat).filter(Chat.id == req.chat_id).first()
    if not chat:
        raise HTTPException(status_code=400, detail="Invalid chat_id")

    # 1️⃣ Save USER message
    save_chat_message(
        db=db,
        chat_id=req.chat_id,
        role="user",
        message=req.message,
    )

    # 2️⃣ Build conversation history
    history = get_chat_messages(db, req.chat_id)

    conversation = ""
    for msg in history:
        conversation += f"{msg.role.upper()}: {msg.message}\n"

    # 3️⃣ Get AI reply via shared Gemini service
    bot_reply = chat_with_gemini(conversation)

    # 4️⃣ Save AI message
    save_chat_message(
        db=db,
        chat_id=req.chat_id,
        role="ai",
        message=bot_reply,
    )

    return {"reply": bot_reply}
