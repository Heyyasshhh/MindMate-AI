# Step-by-Step No-Cost Deployment Guide

Follow this guide to deploy **MindMate AI** live on public URLs using standard free tiers. 

---

## 🛠️ Free Cloud Stack Architecture
* **Frontend**: Next.js 15 on **Vercel** (Global Edge CDN, Git CI/CD).
* **Backend**: FastAPI on **Koyeb** (Free Instance, Dockerfile builder).
* **Database & Auth**: PostgreSQL and User Credentials on **Supabase** (Free Tier database + secure storage).
* **AI Engine**: Google Gemini API via **Google AI Studio** (Free Tier).

---

## 1. Setup Database & Auth on Supabase

Since Koyeb free instances have ephemeral storage (resets on restart), you should connect a persistent PostgreSQL instance. Supabase is the recommended free option.

1. Go to [Supabase](https://supabase.com) and sign up for a free account.
2. Click **New Project** and name it `MindMate AI`. Define a secure database password and choose your nearest region.
3. Once the database is ready, navigate to the **SQL Editor** in the left sidebar.
4. Click **New Query** and paste the following SQL schema to initialize the user-partitioned tables:
   ```sql
   -- Create Users table
   CREATE TABLE IF NOT EXISTS users (
       id UUID PRIMARY KEY,
       username VARCHAR(50) UNIQUE NOT NULL,
       password_hash VARCHAR(255) NOT NULL,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );

   -- Create Journals table
   CREATE TABLE IF NOT EXISTS journals (
       id UUID PRIMARY KEY,
       content TEXT NOT NULL,
       exam_context VARCHAR(100),
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       analysis JSONB NOT NULL,
       user_id UUID REFERENCES users(id) ON DELETE CASCADE
   );

   -- Create Mood Logs table
   CREATE TABLE IF NOT EXISTS mood_logs (
       id UUID PRIMARY KEY,
       mood_score INTEGER NOT NULL CHECK (mood_score BETWEEN 1 AND 10),
       energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),
       sleep_hours REAL CHECK (sleep_hours BETWEEN 0 AND 24),
       study_hours REAL CHECK (study_hours BETWEEN 0 AND 18),
       stress_level INTEGER CHECK (stress_level BETWEEN 1 AND 10),
       note VARCHAR(255),
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       user_id UUID REFERENCES users(id) ON DELETE CASCADE
   );

   -- Indexes for optimized performance
   CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
   CREATE INDEX IF NOT EXISTS idx_journals_user_created ON journals(user_id, created_at DESC);
   CREATE INDEX IF NOT EXISTS idx_mood_logs_user_created ON mood_logs(user_id, created_at DESC);
   ```
5. Click **Run** to execute the queries.
6. Go to **Project Settings** -> **Database** in the left sidebar and copy the **URI Connection String** under "Connection strings" (choose the "Transaction" or "Session" pooler tab, which uses port 5432 or 6543). It looks like this:
   `postgresql://postgres:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres`
   *Note: Save this connection string; you will need it for the backend environment configuration.*

---

## 2. Deploy Backend on Koyeb (FastAPI)

Koyeb offers a free tier for deploying containerized apps directly from GitHub.

1. Push your repository code to GitHub (ensuring `.env`, `.venv`, and `node_modules` are ignored).
2. Create an account at [Koyeb](https://www.koyeb.com).
3. Select **Create App** and choose **GitHub** as the source.
4. Select your `MindMate AI` repository.
5. In the builder settings:
   * **Root Directory**: Set to `backend`
   * **Deploy Type**: Select **Dockerfile** (Koyeb will automatically build the backend using `backend/Dockerfile`).
6. Scroll down to **Environment Variables** and add the following:
   * `ALLOWED_ORIGINS`: `["https://your-frontend-app.vercel.app"]` (Update this with your Vercel URL once deployed, or set `["*"]` initially for debugging).
   * `AI_PROVIDER`: `gemini`
   * `GEMINI_API_KEY`: `your_google_ai_studio_api_key` (Get one for free at [Google AI Studio](https://aistudio.google.com)).
   * `DATABASE_URL`: Paste the Supabase PostgreSQL connection URI string you copied in Step 1.
7. Click **Deploy**. Once successfully deployed, copy your Koyeb public URL (e.g., `https://mindmate-backend-username.koyeb.app`).
8. Confirm the backend is live by opening:
   `https://mindmate-backend-username.koyeb.app/api/v1/health`

---

## 3. Deploy Frontend on Vercel (Next.js)

Vercel is the creator of Next.js and hosts React apps for free.

1. Sign up for a free account at [Vercel](https://vercel.com).
2. Click **Add New** -> **Project** and import your GitHub repository.
3. In the project configurations:
   * **Root Directory**: Select `frontend`.
   * **Framework Preset**: Next.js (automatically detected).
4. Under **Environment Variables**, add:
   * `NEXT_PUBLIC_API_BASE_URL`: Paste your Koyeb backend API URL followed by `/api/v1` (e.g. `https://mindmate-backend-username.koyeb.app/api/v1`).
5. Click **Deploy**. Vercel will build and launch your Next.js frontend.
6. Open the generated Vercel URL (e.g. `https://mindmate-ai.vercel.app`), sign up a new student account, and verify that the seeder, journal analysis, Recharts dashboard, and companion chatbot are working perfectly!
