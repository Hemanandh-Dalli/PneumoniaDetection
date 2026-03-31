from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.db import get_db
from database.crud import get_user_predictions
from database.models import User
from routes.auth import get_current_user
from utils.config import to_public_path

router = APIRouter()


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    predictions = get_user_predictions(db, current_user.id)
    return [
        {
            "id": p.id,
            "predicted_class": p.predicted_class,
            "confidence": p.confidence,
            "created_at": p.created_at,
            "image_path": to_public_path(p.image_path),
            "chat_id": p.chat.id if p.chat else None,
        }
        for p in predictions
    ]
