# Pneumonia Detection Platform

A full-stack AI-assisted web platform for chest X-ray screening that predicts pneumonia classes, explains results in plain language, supports follow-up Q&A, stores patient-wise history, and generates downloadable PDF reports.

## 1. Project Summary

This project combines:
- A **React + Vite frontend** for authentication, image upload, result viewing, history, and conversational follow-up.
- A **FastAPI backend** for authentication, inference, chat, report generation, and persistence.
- A **Keras/TensorFlow model** (`.keras`) for multi-class chest X-ray classification.
- **Grad-CAM visualization** to highlight image regions influencing the model output.
- **Google Gemini API** for simple-language explanation and safety-constrained chat.
- **MySQL + SQLAlchemy** for user, prediction, and chat persistence.

Primary use case:
1. User logs in.
2. Uploads chest X-ray.
3. Receives predicted class + confidence + Grad-CAM heatmap + AI explanation.
4. Asks follow-up questions in chat.
5. Downloads a structured PDF report.
6. Views historical predictions from dashboard/history pages.

## 2. Tech Stack

### Frontend
- React 18
- Vite
- React Router DOM
- Axios
- Material UI (`@mui/material`, `@mui/icons-material`, Emotion)
- Framer Motion

### Backend
- FastAPI
- Uvicorn
- SQLAlchemy
- PyMySQL
- python-jose (JWT)
- passlib + bcrypt (password hashing)
- TensorFlow + Keras
- NumPy
- OpenCV + Pillow
- google-genai (Gemini)
- ReportLab (PDF)
- python-dotenv

## 3. High-Level Architecture

```text
[React Frontend]
  |  (HTTP + JWT)
  v
[FastAPI Backend]
  |- Auth Routes (/register, /login)
  |- Predict Route (/predict)
  |    |- Save upload -> /backend/uploads
  |    |- Run Keras model inference
  |    |- Generate Grad-CAM heatmap
  |    |- Ask Gemini for explanation
  |    |- Save prediction + chat bootstrap in DB
  |
  |- Chat Routes (/chat, /chat/{id})
  |- Report Route (/report) -> PDF stream
  |- History Routes (/my-predictions, /history)
  |
  v
[MySQL Database]
  |- users
  |- predictions
  |- chats
  |- chat_messages
```

## 4. Repository Structure

```text
pneu/
+- backend/
¦  +- main.py
¦  +- .env
¦  +- requirements.txt
¦  +- model/
¦  ¦  +- pneumonia.keras
¦  +- database/
¦  ¦  +- db.py
¦  ¦  +- models.py
¦  ¦  +- crud.py
¦  +- routes/
¦  ¦  +- auth.py
¦  ¦  +- predict.py
¦  ¦  +- chat.py
¦  ¦  +- report.py
¦  ¦  +- history.py
¦  +- services/
¦  ¦  +- model_service.py
¦  ¦  +- gemini_service.py
¦  ¦  +- image_service.py (placeholder)
¦  ¦  +- pdf_service.py (placeholder)
¦  +- uploads/
¦  +- reports/
+- frontend/
¦  +- package.json
¦  +- vite.config.js
¦  +- src/
¦     +- main.jsx
¦     +- App.jsx
¦     +- api/api.js
¦     +- components/
¦     ¦  +- Layout.jsx
¦     ¦  +- Loader.jsx
¦     ¦  +- Navbar.jsx (empty)
¦     ¦  +- ChatBox.jsx (empty)
¦     +- context/ThemeContext.jsx
¦     +- pages/
¦        +- Login.jsx
¦        +- Register.jsx
¦        +- Upload.jsx
¦        +- Result.jsx
¦        +- Dashboard.jsx
¦        +- History.jsx
+- README.md
```

## 5. Environment Configuration

Create `backend/.env` with:

```env
SECRET_KEY=<strong-random-secret>
GEMINI_API_KEY=<your-google-gemini-api-key>
DATABASE_URL=mysql+pymysql://<user>:<password>@localhost:3306/pneumonia_app
```

Notes:
- `SECRET_KEY` signs JWT tokens.
- `GEMINI_API_KEY` is read by `services/gemini_service.py`.
- `DATABASE_URL` is consumed by `database/db.py`.

## 6. Installation and Run Guide

## 6.1 Prerequisites
- Python 3.10+ (recommended 3.10/3.11)
- Node.js 18+
- MySQL Server (running)

## 6.2 Backend Setup

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Start backend:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Backend base URL:
- `http://127.0.0.1:8000`

## 6.3 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend base URL:
- `http://localhost:5173`

## 6.4 CORS
Backend currently allows these origins:
- `http://localhost:5173`
- `http://localhost:5174`
- `http://127.0.0.1:5173`
- `http://127.0.0.1:5174`

## 7. Backend API Reference

## 7.1 Auth

### `POST /register`
Create user account.

Request JSON:
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

Response:
```json
{ "message": "User registered successfully" }
```

### `POST /login`
Login and receive JWT.

Form data (`application/x-www-form-urlencoded`):
- `username`: email
- `password`: password

Response:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

## 7.2 Prediction

### `POST /predict` (JWT required)
Upload chest X-ray and run end-to-end inference.

Request:
- Multipart form-data with file field: `file`

Response fields:
- `prediction_id`
- `chat_id`
- `predicted_class`
- `confidence`
- `explanation`
- `image_path`
- `heatmap_path`

## 7.3 Chat

### `GET /chat/{chat_id}`
Fetch full chat messages for a prediction chat.

### `POST /chat`
Send message and receive Gemini response.

Request JSON:
```json
{
  "chat_id": 1,
  "message": "What precautions should I take?"
}
```

Response:
```json
{ "reply": "..." }
```

## 7.4 History

### `GET /my-predictions` (JWT required)
Return current user predictions sorted latest-first.

### `GET /history` (JWT required)
Alternative history endpoint using same data model.

## 7.5 Report

### `POST /report`
Generate and download PDF report as streamed response.

Request JSON:
```json
{
  "predicted_class": "Pneumonia-Bacterial",
  "confidence": 0.91,
  "explanation": "...",
  "image_path": "uploads/abc.jpg",
  "heatmap_path": "uploads/abc_heatmap.jpg"
}
```

Response:
- `application/pdf`
- `Content-Disposition: attachment; filename=pneumonia_report.pdf`

## 8. Database Design

Defined in `backend/database/models.py`.

### `users`
- `id` (PK)
- `email` (unique)
- `password_hash`
- `is_verified`
- `created_at`

### `predictions`
- `id` (PK)
- `user_id` (FK -> users.id)
- `image_path`
- `predicted_class`
- `confidence`
- `explanation`
- `created_at`

### `chats`
- `id` (PK)
- `prediction_id` (FK -> predictions.id)
- `created_at`

### `chat_messages`
- `id` (PK)
- `chat_id` (FK -> chats.id)
- `role` (`user` / `assistant` / `ai` depending on route flow)
- `message`
- `created_at`

Relations:
- `User 1 -> N Prediction`
- `Prediction 1 -> 1 Chat`
- `Chat 1 -> N ChatMessage`

## 9. ML Inference Workflow

Implemented in `backend/services/model_service.py`.

1. Load model lazily from `model/pneumonia.keras`.
2. Preprocess image:
   - load image
   - resize to `224x224`
   - convert to array
   - expand batch dimension
   - apply VGG16 preprocess
3. Run prediction.
4. Convert logits/probabilities to class index and confidence.
5. Map class index to labels:
   - `Covid-19`
   - `Normal`
   - `Pneumonia-Bacterial`
   - `Pneumonia-Viral`
6. Generate Grad-CAM:
   - identify target conv layer
   - compute gradients with `tf.GradientTape`
   - build heatmap
   - superimpose on original image
   - save `*_heatmap.jpg`

## 10. Explanation and Chat Workflow (Gemini)

Implemented in `backend/services/gemini_service.py`.

### Prediction Explanation
- Called after model inference.
- Prompt constraints:
  - simple language
  - max lines
  - no treatment advice

### Follow-up Chat
- Conversation history assembled from DB messages.
- Prompt constraints include:
  - simple language
  - max 4 lines
  - no diagnosis
  - no prescribing medicine
  - suggest precautions and when to consult doctor

Failure fallback:
- If Gemini call fails, route returns safe fallback text.

## 11. Frontend Functional Workflow

## 11.1 Routing and Auth Guard
- Routes: `/login`, `/register`, `/`, `/dashboard`, `/result`, `/history`
- `PrivateRoute` checks JWT in `localStorage`.
- Axios interceptor adds `Authorization: Bearer <token>` for API calls.

## 11.2 User Journey
1. Register user.
2. Login and store JWT token.
3. Upload image from `Upload.jsx` -> `POST /predict`.
4. Navigate to `Result.jsx` with prediction payload.
5. Render:
   - original image
   - Grad-CAM heatmap
   - diagnosis + confidence + severity label
6. Load chat history (`GET /chat/{id}`).
7. Send chat prompts (`POST /chat`).
8. Download report (`POST /report`, blob download).
9. Dashboard/history fetch previous predictions (`GET /my-predictions`).

## 12. Security and Compliance Notes

- Passwords are hashed with passlib + bcrypt.
- JWT is used for protected endpoints.
- Do not hardcode or expose API keys.
- This system is an assistive tool and should not be used as a standalone clinical diagnosis engine.

## 13. Known Gaps / Improvement Backlog

- Add DB migrations (Alembic) and automated table creation strategy.
- Add request/response schema validation coverage for all routes.
- Normalize chat role naming (`assistant` vs `ai`) for consistency.
- Move static paths and base URLs to environment configs in frontend.
- Add tests:
  - backend route tests
  - service unit tests
  - frontend component/integration tests
- Add containerized deployment (`Dockerfile` + `docker-compose`).
- Add CI pipeline (lint + tests + build).
- Add rate limiting and audit logging for security hardening.

## 14. Troubleshooting

### Backend fails to connect DB
- Verify MySQL is running.
- Verify `DATABASE_URL` credentials/database.
- Ensure database `pneumonia_app` exists.

### `401 Invalid token`
- Re-login from frontend.
- Ensure Axios sends Bearer token.
- Ensure backend `SECRET_KEY` matches token signing key.

### Gemini explanation fails
- Verify `GEMINI_API_KEY` in `backend/.env`.
- Check outbound network access and API quota.

### Model loading error
- Ensure `backend/model/pneumonia.keras` exists.
- Ensure TensorFlow/Keras versions match model serialization expectations.

### Image not displayed
- Ensure backend is running and serves `/uploads` static directory.
- Ensure frontend constructs image URL as `http://127.0.0.1:8000/<image_path>`.

## 15. License / Disclaimer

Add your project license here (MIT/Apache-2.0/etc.).

Medical disclaimer:
This project is intended for educational and decision-support use only and not for definitive medical diagnosis or treatment decisions.
