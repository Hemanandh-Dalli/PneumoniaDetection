# Deployment Guide

## Architecture

- Frontend: Vercel static build from `frontend/`
- Backend: Vercel Python serverless function at `api/index.py`
- Database: Supabase Postgres
- File storage: Supabase Storage bucket
- AI analysis: Google Gemini

## What Changed

The old TensorFlow plus local-file backend was removed because it is not a practical fit for Vercel serverless deployment. The app now:

1. Uploads X-ray images to Supabase Storage
2. Stores users, predictions, chats, and messages in Supabase
3. Uses a Vercel Python API for auth, prediction, chat, history, and PDF reports
4. Uses Gemini for image-based screening assessment and follow-up chat

## Required Environment Variables

Set these in the Vercel project:

```env
SECRET_KEY=change-me-to-a-long-random-secret
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
SUPABASE_BUCKET=xrays
ALLOWED_ORIGINS=https://your-project.vercel.app,http://localhost:5173,http://127.0.0.1:5173
VITE_API_BASE_URL=/api
```

## Supabase Setup

1. Create a new Supabase project.
2. Open the SQL Editor.
3. Run the SQL in `supabase/schema.sql`.
4. Open `Storage`.
5. Create a public bucket named `xrays` or change `SUPABASE_BUCKET` to match your bucket name.

## Vercel Setup

1. Import this GitHub repo into Vercel.
2. Keep the root project configuration.
3. Add the environment variables listed above.
4. Deploy.

The current `vercel.json` builds the React app from `frontend/` and rewrites `/api/*` to the Python function in `api/index.py`.

## Verification

After deployment:

1. Open the Vercel app URL.
2. Register a user.
3. Log in.
4. Upload a chest X-ray under 4 MB.
5. Confirm you receive an assessment and explanation.
6. Open dashboard and history.
7. Send a follow-up message in chat.
8. Download the PDF report.

## Important Notes

- Vercel functions have body-size and execution limits. Keep uploaded images reasonably small.
- This deployment no longer generates a Grad-CAM heatmap.
- This remains an assistive screening workflow and not a confirmed medical diagnosis system.
