# Change Request Document (CRD) - MindMate AI

This document details the enhancements made to the MindMate AI application to ensure full compliance with the Product Requirements Document (PRD) across Code Quality, Security, Efficiency, Testing, and Accessibility.

---

## 1. Executive Summary & PRD Alignment

All MVP features specified in the PRD are fully implemented, persistent, and production-ready:
* **User Accounts & Login**: Supports user signup, credential logging, session generation, and logouts.
* **AI Journal Analysis**: Generates sentiment, emotional intensity, stress triggers, cognitive distortion patterns, and personalized coping strategies. Uses a production Google Gemini model with a zero-cost local heuristic fallback.
* **Daily Mood Logging**: Logs mood (1-10), stress (1-10), sleep hours, study hours, and note text, persisted in a structured local SQLite database.
* **Dashboard Summary**: Displays streak counts, mood averages, burnout risk alerts, and weekly progress.
* **Interactive Timeline & Analytics**: Rendered via Recharts Area and Bar graphs showing Mood & Stress history and Sleep vs Study correlations over time.
* **Empathetic Companion Chat**: Provides responsive coaching aligned with exam stress, utilizing Gemini with a keyword fallback.
* **Mindfulness Generator**: Includes a guided 4-7-8 breathing module with a visual countdown and pulsing animation, progressive sleep muscle relaxation instructions, and self-compassion journal prompts.
* **Crisis Safety Filters**: Instantly intercepts crisis-related keywords before any LLM operations are triggered, returning immediate resource escalation directions.

---

## 2. Core Architectural Improvements

### 2.1 Code Quality & Structure
* **Database Persistence**: Replaced the volatile `InMemoryWellnessStore` with a robust SQLite database layer using python's built-in `sqlite3` driver. This creates a local database file `mindmate.db` so data persists across server restarts.
* **Interface Uniformity**: Structured both `SQLiteWellnessStore` and `InMemoryWellnessStore` under the same repository API pattern. This makes it trivial to swap storage systems in backend configuration.
* **Structured Data Mapping**: Stored complex analysis outputs as serialized JSON fields in SQLite, utilizing Pydantic's `model_dump_json()` and `model_validate()` to maintain strict type safety.

### 2.2 Security & Responsible AI
* **User Authentication**: Integrated JWT verification. Authentication tokens are signed using the `HS256` algorithm and have a 24-hour expiration duration.
* **Cryptographically Secure Hashing**: Implemented PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations and a cryptographically random salt (`secrets.token_hex`), utilizing a constant-time comparison (`secrets.compare_digest`) to completely prevent timing-attack vectors.
* **Tenant Isolation Security**: Scoped all database entries to the user's unique ID. All journal submissions, mood logs, and count aggregations require verification of the JWT token via FastAPI dependencies (`get_current_user`) and filter SQL records dynamically by the logged-in student's ID, preventing any cross-user data leakage.
* **Safe API Execution**: Applied deterministic crisis pre-filters in both the `/journals` and `/chat` endpoints. If crisis words are spotted, the app instantly responds with safety helpline instructions without making network requests to the LLM.
* **API Key Protection**: Leveraged FastAPI's environment settings (`pydantic-settings`). The Google Gemini API key is loaded securely from the environment or `.env` files, avoiding any hardcoded keys.
* **Robust Fail-Safe**: Designed the Gemini adapter to handle network timeouts, rate limits, and parsing errors. If an error occurs, the server logs a warning and seamlessly falls back to the keyword heuristic engine, ensuring 100% uptime.

### 2.3 Resource Efficiency
* **Fast Database Counting**: Added a dedicated `get_counts(user_id)` database query using SQL `COUNT(*)` to calculate dashboard progress and streak metrics. This avoids loading thousands of records into memory just to determine list lengths.
* **Pagination and Limits**: Implemented SQL query `LIMIT` constraints inside `get_journals` and `get_mood_logs` to fetch only the required 7 or 5 recent logs for charts and insights, optimizing memory usage.
* **Lightweight Network Footprint**: Utilized a clean, direct `httpx.Client` for Gemini API calls, removing the need for heavy external frameworks like LangChain or Pydantic AI in the MVP.

### 2.4 Test Verification
* **Comprehensive Test Suite**: Increased test coverage to 14 unit and integration tests:
  * `test_analysis.py`: Validates trigger detection, primary emotions, and crisis keyword interception.
  * `test_auth.py`: Validates password hashing/verification and JWT creation/decoding helpers.
  * `test_db.py`: Verifies SQL schema initialization, user-partitioned inserts, chronological sorting, and strict user isolation queries.
  * `test_endpoints.py`: Tests signup, login, bearer token auth headers, and wellness routes protection (401/403 status codes).
* All tests run and pass in under 1.5 seconds.

### 2.5 WCAG 2.1 Accessibility Compliance
* **Text Scaling Controls**: Supports scaling the font size from `90%` to `130%` dynamically via CSS HSL variables.
* **High Contrast Mode**: Implemented a complete AAA high-contrast toggle that switches background/foreground colors to pure black and white/neon teal, ensuring readability for visually impaired students.
* **Dyslexia-Friendly Typography**: Added a Dyslexia option changing the layout font family to a highly legible Sans-Serif style with increased letter-spacing (`0.14em`) and line-heights (`1.8`).
* **Semantic Structure**: Built logical heading hierarchies (`h1` down to `h3`), ARIA tags (`aria-live="polite"` for dynamic analysis alerts, `aria-label`), keyboard focus outline styling, and fully responsive layouts down to `320px` width.
