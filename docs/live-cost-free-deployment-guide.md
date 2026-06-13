# MindMate AI Step-by-Step Deployment Guide

This guide deploys the current MindMate AI MVP for free:

- Frontend: Vercel free tier
- Backend: Koyeb free tier, with Render as an alternative
- AI: built-in zero-cost heuristic engine
- Database: in-memory for MVP demo, Supabase planned for persistence

The current backend stores data in memory. That is fine for a hackathon/demo, but data resets when the backend restarts.

## Prerequisites

Create free accounts:

1. GitHub: https://github.com
2. Vercel: https://vercel.com
3. Koyeb: https://www.koyeb.com

Optional alternatives:

1. Render: https://render.com
2. Supabase: https://supabase.com
3. Google AI Studio: https://aistudio.google.com

## Step 1: Check The Project Locally

From the project root:

```bash
cd "Y:\Projects\MindMate AI"
```

Backend local run:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open this backend health URL:

```text
http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "mindmate-ai"
}
```

Frontend local run in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

Test:

1. Submit a journal entry.
2. Save a mood log.
3. Send a companion chat message.
4. Confirm the dashboard updates.

## Step 2: Create A GitHub Repository

In GitHub:

1. Click **New repository**.
2. Name it `mindmate-ai`.
3. Keep it public or private.
4. Do not add a README from GitHub because this project already has one.
5. Create the repository.

From the project root:

```bash
git init
git add .
git commit -m "Initial MindMate AI MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/mindmate-ai.git
git push -u origin main
```

Before pushing, make sure secret files are not committed:

```bash
git status
```

Do not commit:

- `.env`
- `.env.local`
- `.venv`
- `node_modules`
- `.next`

## Step 3: Deploy Backend On Koyeb

Koyeb is recommended for the FastAPI backend because the included Dockerfile works cleanly.

1. Log in to Koyeb.
2. Click **Create App**.
3. Choose **GitHub** as the deployment source.
4. Select your `mindmate-ai` repository.
5. Set the service root or build context to:

```text
backend
```

6. Choose Dockerfile deployment.
7. Confirm Dockerfile path:

```text
backend/Dockerfile
```

8. Set service port:

```text
8000
```

9. Add environment variables:

```env
ALLOWED_ORIGINS=["https://your-vercel-app.vercel.app"]
AI_PROVIDER=heuristic
GEMINI_API_KEY=
```

At this stage you do not know the final Vercel URL yet. You can temporarily use:

```env
ALLOWED_ORIGINS=["http://localhost:3000"]
```

After the frontend deploys, return to Koyeb and replace it with the real Vercel URL.

10. Click **Deploy**.
11. Copy the deployed backend URL. It will look like:

```text
https://your-app-name.koyeb.app
```

12. Test backend health:

```bash
curl https://your-app-name.koyeb.app/api/v1/health
```

Expected:

```json
{"status":"ok","service":"mindmate-ai"}
```

## Step 4: Deploy Frontend On Vercel

1. Log in to Vercel.
2. Click **Add New Project**.
3. Import your GitHub `mindmate-ai` repository.
4. Set **Root Directory** to:

```text
frontend
```

5. Keep framework preset as **Next.js**.
6. Add this environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-app-name.koyeb.app/api/v1
```

7. Click **Deploy**.
8. Copy the deployed frontend URL. It will look like:

```text
https://mindmate-ai.vercel.app
```

## Step 5: Update Backend CORS

Return to Koyeb after Vercel is deployed.

Update backend environment variable:

```env
ALLOWED_ORIGINS=["https://mindmate-ai.vercel.app"]
```

Redeploy or restart the Koyeb backend service.

This allows the browser frontend to call the backend safely.

## Step 6: Run Live Smoke Tests

Open your Vercel frontend URL.

Test journal analysis:

1. Paste this demo journal:

```text
I studied only 5 hours today. Everyone else seems ahead. I feel guilty and anxious after my mock test.
```

2. Click **Analyze journal**.
3. Confirm the app shows:

- Primary emotion
- Risk level
- Triggers
- Coping strategies

Test mood logging:

1. Set mood score.
2. Set stress level.
3. Enter sleep and study hours.
4. Click **Save mood**.
5. Confirm dashboard values update.

Test chat:

1. Send:

```text
I feel like quitting.
```

2. Confirm the companion replies with a supportive next step.

Test crisis guardrail:

1. Send a crisis-like test message only as a controlled demo.
2. Confirm the app displays emergency/support guidance.

## Step 7: Optional Render Backend Deployment

Use Render if Koyeb is unavailable.

1. Log in to Render.
2. Click **New**.
3. Choose **Web Service**.
4. Connect the GitHub repository.
5. Set root directory:

```text
backend
```

6. Set build command:

```bash
pip install -r requirements.txt
```

7. Set start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

8. Add environment variables:

```env
ALLOWED_ORIGINS=["https://your-vercel-app.vercel.app"]
AI_PROVIDER=heuristic
GEMINI_API_KEY=
```

9. Deploy.
10. Use the Render backend URL in Vercel:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-render-app.onrender.com/api/v1
```

Render free services may sleep after inactivity. The first request after sleep can be slow.

## Step 8: Optional Supabase Persistence

Use this before onboarding real users.

1. Create a Supabase project.
2. Enable email/password auth.
3. Create these tables:

```text
profiles
journal_entries
mood_logs
chat_messages
wellness_insights
```

4. Add backend environment variables:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

5. Replace `InMemoryWellnessStore` in `backend/app/services/storage.py` with a Supabase/PostgreSQL repository.
6. Add row-level security policies before real users store private journal data.

## Step 9: Optional Gemini AI Upgrade

The MVP works without paid AI. To add Gemini later:

1. Create an API key in Google AI Studio.
2. Add backend environment variables:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_api_key
```

3. Add a Gemini adapter in the backend AI service.
4. Keep deterministic crisis detection before any LLM call.
5. Keep heuristic fallback for outages and quota limits.

## Step 10: Final Production Checklist

Before sharing publicly:

- Frontend loads on Vercel.
- Backend health endpoint returns `ok`.
- Journal analysis works from the live frontend.
- Mood logging works from the live frontend.
- Chat works from the live frontend.
- CORS is restricted to the real Vercel domain.
- No secret keys are committed to GitHub.
- Demo users understand this is not medical care.
- Real user launch waits for auth, persistence, privacy policy, and consent.

## Common Errors

### Frontend says backend unavailable

Check Vercel environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend-url/api/v1
```

Then redeploy the frontend.

### Browser blocks API requests

Check backend `ALLOWED_ORIGINS`.

It must include the exact Vercel URL:

```env
ALLOWED_ORIGINS=["https://mindmate-ai.vercel.app"]
```

### Backend health works but frontend does not update

Open browser developer tools and check the Network tab. Confirm requests go to:

```text
https://your-backend-url/api/v1
```

### Koyeb or Render cold start feels slow

Free services may sleep. Wait for the first request to finish, then test again.

## Recommended Free Demo Setup

For the fastest zero-cost live demo:

1. GitHub repository.
2. Koyeb backend using `AI_PROVIDER=heuristic`.
3. Vercel frontend using `NEXT_PUBLIC_API_BASE_URL`.
4. No real personal journal data until Supabase Auth and database security are added.
