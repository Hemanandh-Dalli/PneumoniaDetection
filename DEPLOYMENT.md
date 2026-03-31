# Local Run Guide

## Architecture

- Frontend: React + Vite on localhost
- Backend: FastAPI on localhost
- Database: local MySQL

This project is configured to run fully on your machine without Vercel, Render, or Supabase.

## Backend Setup

1. Make sure MySQL is running locally.
2. Create a database named `pneumonia_app`.
3. Update `backend/.env` if your local MySQL username or password is different.

Default local database URL:

```env
DATABASE_URL=mysql+pymysql://root:mysql1215?@localhost:3306/pneumonia_app
```

Start the backend:

```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Frontend Setup

The frontend uses the local backend by default through `frontend/.env.example`.

Run it with:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

## Local Environment Values

Backend `backend/.env`:

```env
SECRET_KEY=change-me-to-a-long-random-secret
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=mysql+pymysql://root:mysql1215?@localhost:3306/pneumonia_app
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Frontend `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Notes

- Uploaded images are stored locally in `backend/uploads/`
- Generated PDF reports are created locally
- The TensorFlow model is loaded from `backend/model/pneumonia.keras`
