# Deployment Guide

## Architecture

- Frontend: Vercel
- Backend: Render
- Database: hosted MySQL

Vercel should host only the React frontend. The FastAPI backend uses TensorFlow, file uploads, and local static files, so it should run on Render instead of Vercel serverless functions.

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
DATABASE_URL=mysql+pymysql://user:password@host:3306/pneumonia_app
ALLOWED_ORIGINS=https://your-project.vercel.app
```

You can include multiple frontend origins in `ALLOWED_ORIGINS` by separating them with commas.

## Important limitation

Uploads are currently stored in `backend/uploads/`. On free hosting, local disk is not durable across restarts or redeploys. This is acceptable for a demo, but long-term hosting should move uploads and generated images to object storage.
