# MindMate AI

MindMate AI is a premium, exam-aware emotional wellness companion designed specifically for students preparing for high-stakes competitive examinations (NEET, JEE, UPSC, GATE, CAT, etc.).

The platform helps students reflect honestly, track daily mood, balance study and sleep schedules, identify burnout patterns, and receive supportive, empathetic coaching.

---

## 🚀 Key Features

* **Secure Student Auth**: Signup, login, and secure sessions via JSON Web Tokens (JWT).
* **Private Partitioned Data**: All reflections and mood logs are secured to the specific authenticated student's ID, ensuring total privacy.
* **AI Journal Reflector**: Extracts primary emotions, intensity, exam triggers (mock tests, peer pressure, parents), cognitive distortions, and personalized coping strategies.
* **Persistent Mood Log**: Track daily mood, stress levels, study hours, and sleep patterns.
* **Interactive Data Dashboard**: Live Recharts Area and Bar charts displaying Mood & Stress trend lines and Study vs Sleep correlation.
* **Empathetic Companion Chat**: Safe, non-clinical supportive chat utilizing AI or local heuristic fallback.
* **Mindfulness Suite**: Guided 4-7-8 breathing module with a visual countdown and pulsing animation, progressive muscle relaxation instructions, and self-compassion journal prompts.
* **Robust Safety Boundaries**: Deterministic pre-checks that capture crisis keywords instantly and escalate to support helplines.
* **Full WCAG 2.1 Accessibility**: Features a dynamic accessibility control panel supporting:
  * **Dark Mode** / Light Mode toggling.
  * **High Contrast AAA Mode** (pure black/white contrast ratios).
  * **Dyslexia-Friendly Typography** (widened character spacing and specific weights).
  * **Interactive Font Scaling** (Small, Medium, Large, Extra Large).

---

## 📂 Repository Structure

```text
backend/
  app/
    api/          FastAPI endpoints
    core/         Configuration settings
    models/       Pydantic validation schemas
    services/     analysis, safety, auth encryption, database persistence, storage wrappers
  tests/          pytest test suite (auth, db, analysis, routes)
frontend/
  app/            Next.js app router & layout configurations
  components/     WellnessApp React UI and Recharts charts
  lib/            HTTP API client wrappers
docs/
  change_request_document.md       Detailed CRD mapping compliance
  no-cost-deployment-guide.md      Step-by-step zero-cost hosting guide
```

---

## ⚙️ API Schema

* **Auth**:
  - `POST /api/v1/auth/signup`: Create a new account.
  - `POST /api/v1/auth/login`: Authenticate and obtain JWT token.
* **Wellness (Requires Authorization Header: `Bearer <token>`)**:
  - `GET /api/v1/health`: API status checker (public).
  - `POST /api/v1/journals`: Submit and analyze a journal entry.
  - `GET /api/v1/journals`: Retrieve journal history.
  - `POST /api/v1/mood-logs`: Log mood, sleep, study, and stress.
  - `GET /api/v1/mood-logs`: Retrieve logged stats history.
  - `GET /api/v1/dashboard`: Retrieve aggregated dashboard summaries.
  - `POST /api/v1/chat`: Interact with the empathetic coaching companion.

---

## 🛠️ Local Development Setup

### 1. Backend (FastAPI)

Prerequisites: Python 3.10+ installed.

1. Navigate to backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend` directory (optional for Gemini):
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_google_ai_studio_api_key
   DB_PATH=mindmate.db
   ```
   *Note: If `GEMINI_API_KEY` is omitted, the backend will automatically and gracefully fall back to the zero-cost local heuristic keyword engine, keeping the app 100% functional out-of-the-box.*
5. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`. Confirm health check:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

### 2. Frontend (Next.js)

Prerequisites: Node.js 18+ installed.

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 Running Tests

A complete suite of unit and integration tests is included. Run the following command inside the `backend` folder to execute all 14 tests:

```bash
cd backend
.venv\Scripts\pytest
```

---

## ⚙️ How SQLite Storage Works

MindMate AI uses an SQLite database (`mindmate.db`) by default for local development.
* All logs are saved instantly.
* To clear or reset the local database during testing, you can delete the `mindmate.db` file in the `backend` folder.
* For visual demonstration, log in and click the **"Seed 7 Days of Demo Logs"** button in the dashboard header. This will automatically write a realistic week of sleep, study, and mood logs to the database, allowing you to view the Recharts charts immediately!

---

## 🛡️ Safety Warning

MindMate AI is an emotional wellness support tool and is **not** a replacement for professional therapy, clinical diagnosis, or medical emergency treatment. The application includes a deterministic crisis detection safety net. If phrases indicating self-harm or severe crisis are detected, the app blocks normal conversation and displays helpline resources.
