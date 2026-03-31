from sqlalchemy.orm import Session
from typing import List, Optional

from . import models


# -------------------------
# USER
# -------------------------

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, email: str, password: str) -> models.User:
    user = models.User(email=email, password_hash=password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# -------------------------
# PREDICTION
# -------------------------

def save_prediction(
    db: Session,
    user_id: int,
    image_path: str,
    predicted_class: str,
    confidence: float,
    explanation: str,
) -> models.Prediction:
    prediction = models.Prediction(
        user_id=user_id,
        image_path=image_path,
        predicted_class=predicted_class,
        confidence=confidence,
        explanation=explanation,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


# -------------------------
# CHAT
# -------------------------

def create_chat(db: Session, prediction_id: int) -> models.Chat:
    chat = models.Chat(
        prediction_id=prediction_id,
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def save_chat_message(
    db: Session,
    chat_id: int,
    role: str,
    message: str,
) -> models.ChatMessage:
    chat_message = models.ChatMessage(
        chat_id=chat_id,
        role=role,
        message=message,
    )
    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)
    return chat_message


# -------------------------
# FETCHING DATA
# -------------------------

def get_chat_messages(db: Session, chat_id: int) -> List[models.ChatMessage]:
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.chat_id == chat_id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )


def get_user_predictions(db: Session, user_id: int) -> List[models.Prediction]:
    return (
        db.query(models.Prediction)
        .filter(models.Prediction.user_id == user_id)
        .order_by(models.Prediction.created_at.desc())
        .all()
    )


# -------------------------
# DELETE (SOFT LOGIC READY)
# -------------------------

def delete_prediction(db: Session, prediction_id: int):
    prediction = db.query(models.Prediction).filter(models.Prediction.id == prediction_id).first()
    if prediction:
        db.delete(prediction)
        db.commit()

