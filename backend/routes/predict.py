from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import uuid
import traceback

from database.db import get_db
from database.models import User, Prediction
from database.crud import (
    save_prediction,
    create_chat,
    save_chat_message,
    get_user_predictions,
)

from routes.auth import get_current_user

from services.model_service import predict as model_predict
from services.gemini_service import explain_prediction

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------
# 🔥 PREDICT (JWT PROTECTED)
# ---------------------------------------------------
@router.post("/predict")
async def predict_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    step = "init"
    try:
        user_id = current_user.id

        # -------------------------
        # SAVE IMAGE
        # -------------------------
        step = "save_image"
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # -------------------------
        # MODEL PREDICTION + GRAD-CAM
        # -------------------------
        step = "model_predict"
        predicted_class, confidence, heatmap_path = model_predict(file_path)
        confidence = float(confidence)

        # -------------------------
        # GEMINI EXPLANATION
        # -------------------------
        step = "gemini_explanation"
        explanation = explain_prediction(
            predicted_class,
            confidence,
            max_lines=8,
        )

        # -------------------------
        # SAVE PREDICTION
        # -------------------------
        step = "save_prediction"
        prediction = save_prediction(
            db=db,
            user_id=user_id,
            image_path=file_path,
            predicted_class=predicted_class,
            confidence=confidence,
            explanation=explanation,
        )

        # -------------------------
        # CREATE CHAT
        # -------------------------
        step = "create_chat"
        chat = create_chat(
            db=db,
            prediction_id=prediction.id,
        )

        # -------------------------
        # SAVE FIRST ASSISTANT MESSAGE
        # -------------------------
        step = "save_chat_message"
        save_chat_message(
            db=db,
            chat_id=chat.id,
            role="assistant",
            message=explanation,
        )

        # -------------------------
        # RESPONSE
        # -------------------------
        return {
            "prediction_id": prediction.id,
            "chat_id": chat.id,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "explanation": explanation,
            "image_path": file_path,
            "heatmap_path": heatmap_path,
        }

    except Exception as e:
        print("PREDICT ERROR at step:", step)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"predict_failed:{step}: {str(e)}",
        )


# ---------------------------------------------------
# 📊 DASHBOARD - MY PREDICTIONS
# ---------------------------------------------------
@router.get("/my-predictions")
def my_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    predictions = (
        db.query(Prediction)
        .filter(Prediction.user_id == current_user.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )

    return [
        {
            "id": p.id,
            "predicted_class": p.predicted_class,
            "confidence": p.confidence,
            "created_at": p.created_at,
            "image_path": p.image_path,
            "chat_id": p.chat.id if p.chat else None,
        }
        for p in predictions
    ]

