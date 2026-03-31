# Deployment Guide

## Architecture

- Frontend: Vercel
- Backend: Render
- Database: Supabase Postgres

Vercel should host only the React frontend. The FastAPI backend uses TensorFlow, file uploads, and local static files, so it should run on Render instead of Vercel serverless functions.

## Deployment Order

1. Create the Supabase project and copy the Postgres connection string.
2. Deploy the FastAPI backend to Render with the Supabase `DATABASE_URL`.
3. Deploy the React frontend to Vercel with `VITE_API_BASE_URL` pointing at the Render backend.
4. Verify auth, prediction, history, and report generation against the deployed URLs.

## Supabase Setup

1. Create a new Supabase project.
2. Open `Project Settings -> Database`.
3. Copy the Postgres connection string and convert it to SQLAlchemy format if needed.

Example:

```env
DATABASE_URL=postgresql+psycopg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

The backend now creates tables on startup, so the first Render deploy will initialize the schema automatically.

## Frontend on Vercel

The repo includes a root `vercel.json` that builds the `frontend/` app.

Set this environment variable in Vercel:

```env
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

## Backend on Render

The repo includes a root `render.yaml` that points Render at `backend/`.

Set these environment variables in Render:

```env
SECRET_KEY=change-me-to-a-long-random-secret
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=postgresql+psycopg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
ALLOWED_ORIGINS=https://your-project.vercel.app
```

You can include multiple frontend origins in `ALLOWED_ORIGINS` by separating them with commas.

Render service settings:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

After the first successful deploy, confirm the backend health endpoint:

```text
https://your-render-service.onrender.com/health
```

## Important limitation

Uploads are currently stored in `backend/uploads/`. On free hosting, local disk is not durable across restarts or redeploys. This is acceptable for a demo, but long-term hosting should move uploads and generated images to object storage.

## Post-Deploy Verification

1. Open the Vercel frontend URL.
2. Register a test user.
3. Log in and upload a sample X-ray.
4. Confirm the prediction response returns `image_path` and `heatmap_path`.
5. Open dashboard/history and verify rows are being read from Supabase.
6. Download a PDF report and confirm it includes available images.
