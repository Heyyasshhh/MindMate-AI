"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiGet, apiPost, DashboardSummary, JournalEntry, MoodLog, RiskLevel } from "@/lib/api";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

type ChatResponse = {
  response: string;
  suggested_action?: string;
  risk_level: RiskLevel;
  crisis_detected: boolean;
};

const fallbackDashboard: DashboardSummary = {
  mood_average: 0,
  journal_streak: 0,
  burnout_risk: "low",
  wellness_progress: 0,
  insights: ["Start with one honest journal entry to generate your first insight."],
  recent_emotions: []
};

export function WellnessApp() {
  // Auth state
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const [authUsername, setAuthUsername] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authView, setAuthView] = useState<"login" | "signup">("login");
  const [authError, setAuthError] = useState<string | null>(null);

  // Wellness data state
  const [dashboard, setDashboard] = useState<DashboardSummary>(fallbackDashboard);
  const [moodLogs, setMoodLogs] = useState<MoodLog[]>([]);
  const [journals, setJournals] = useState<JournalEntry[]>([]);
  
  const [journalText, setJournalText] = useState("");
  const [journal, setJournal] = useState<JournalEntry | null>(null);
  
  const [moodScore, setMoodScore] = useState(6);
  const [stressLevel, setStressLevel] = useState(5);
  const [sleepHours, setSleepHours] = useState(7);
  const [studyHours, setStudyHours] = useState(5);
  const [moodNote, setMoodNote] = useState("");
  
  const [chatText, setChatText] = useState("");
  const [chat, setChat] = useState<ChatResponse | null>(null);
  const [status, setStatus] = useState("Ready");

  // Accessibility State
  const [darkMode, setDarkMode] = useState(false);
  const [highContrast, setHighContrast] = useState(false);
  const [dyslexiaFont, setDyslexiaFont] = useState(false);
  const [fontScale, setFontScale] = useState(1.0);

  // Mindfulness State
  const [activeMindfulness, setActiveMindfulness] = useState<string | null>(null);
  const [breathingPhase, setBreathingPhase] = useState<"Inhale" | "Hold" | "Exhale">("Inhale");
  const [breathingSeconds, setBreathingSeconds] = useState(4);

  // SSR hydration safeguard
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);

    // Load accessibility settings from localStorage
    const localDark = localStorage.getItem("mindmate-dark") === "true";
    const localHC = localStorage.getItem("mindmate-hc") === "true";
    const localDyslexia = localStorage.getItem("mindmate-dyslexia") === "true";
    const localScale = parseFloat(localStorage.getItem("mindmate-scale") || "1.0");

    setDarkMode(localDark);
    setHighContrast(localHC);
    setDyslexiaFont(localDyslexia);
    setFontScale(localScale);
    
    // Load auth token
    const localToken = localStorage.getItem("mindmate-token");
    const localUser = localStorage.getItem("mindmate-username");
    if (localToken && localUser) {
      setToken(localToken);
      setUsername(localUser);
    }
  }, []);

  // Fetch user data once token is set/changed
  useEffect(() => {
    if (token) {
      refreshData(token);
    }
  }, [token]);

  // Sync accessibility classes
  useEffect(() => {
    if (!mounted) return;
    if (darkMode) document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
    localStorage.setItem("mindmate-dark", String(darkMode));
  }, [darkMode, mounted]);

  useEffect(() => {
    if (!mounted) return;
    if (highContrast) document.documentElement.classList.add("high-contrast");
    else document.documentElement.classList.remove("high-contrast");
    localStorage.setItem("mindmate-hc", String(highContrast));
  }, [highContrast, mounted]);

  useEffect(() => {
    if (!mounted) return;
    if (dyslexiaFont) document.documentElement.classList.add("dyslexia-font");
    else document.documentElement.classList.remove("dark"); // resets if needed, or dyslexia-font
    localStorage.setItem("mindmate-dyslexia", String(dyslexiaFont));
  }, [dyslexiaFont, mounted]);

  useEffect(() => {
    if (!mounted) return;
    document.documentElement.style.setProperty("--font-scale", String(fontScale));
    localStorage.setItem("mindmate-scale", String(fontScale));
  }, [fontScale, mounted]);

  // Mindfulness 4-7-8 Breathing logic
  useEffect(() => {
    if (activeMindfulness !== "breathing") return;

    let elapsed = 0;
    const interval = setInterval(() => {
      elapsed = (elapsed + 1) % 19;
      if (elapsed < 4) {
        setBreathingPhase("Inhale");
        setBreathingSeconds(4 - elapsed);
      } else if (elapsed < 11) {
        setBreathingPhase("Hold");
        setBreathingSeconds(11 - elapsed);
      } else {
        setBreathingPhase("Exhale");
        setBreathingSeconds(19 - elapsed);
      }
    }, 1000);

    setBreathingPhase("Inhale");
    setBreathingSeconds(4);

    return () => clearInterval(interval);
  }, [activeMindfulness]);

  async function refreshData(activeToken = token) {
    if (!activeToken) return;
    try {
      const summary = await apiGet<DashboardSummary>("/dashboard");
      setDashboard(summary);
      
      const logs = await apiGet<MoodLog[]>("/mood-logs");
      setMoodLogs([...logs].reverse()); // Chronological for charts
      
      const jEntries = await apiGet<JournalEntry[]>("/journals");
      setJournals(jEntries);
      if (jEntries.length > 0) {
        setJournal(jEntries[0]);
      }
    } catch (err) {
      console.error("Error loading dashboard data:", err);
      // Auto logout on token expiration
      if (err instanceof Error && err.message.includes("401")) {
        handleLogout();
      } else {
        setDashboard(fallbackDashboard);
      }
    }
  }

  const riskLabel = useMemo(() => dashboard.burnout_risk.toUpperCase(), [dashboard.burnout_risk]);

  async function handleLogin(e: FormEvent) {
    e.preventDefault();
    setAuthError(null);
    setStatus("Verifying credentials...");
    try {
      const result = await apiPost<{ access_token: string }>(
        "/auth/login",
        { username: authUsername, password: authPassword }
      );
      localStorage.setItem("mindmate-token", result.access_token);
      localStorage.setItem("mindmate-username", authUsername);
      setToken(result.access_token);
      setUsername(authUsername);
      setAuthPassword("");
      setStatus("Authenticated");
    } catch {
      setAuthError("Incorrect username or password. Please try again.");
      setStatus("Auth failed");
    }
  }

  async function handleSignup(e: FormEvent) {
    e.preventDefault();
    setAuthError(null);
    setStatus("Registering new student...");
    try {
      await apiPost("/auth/signup", { username: authUsername, password: authPassword });
      
      // Log in automatically
      const result = await apiPost<{ access_token: string }>(
        "/auth/login",
        { username: authUsername, password: authPassword }
      );
      localStorage.setItem("mindmate-token", result.access_token);
      localStorage.setItem("mindmate-username", authUsername);
      setToken(result.access_token);
      setUsername(authUsername);
      setAuthPassword("");
      setStatus("Registered and logged in");
    } catch {
      setAuthError("Registration failed. Username may be taken, or password too short (min 6 chars).");
      setStatus("Signup failed");
    }
  }

  function handleLogout() {
    localStorage.removeItem("mindmate-token");
    localStorage.removeItem("mindmate-username");
    setToken(null);
    setUsername(null);
    setDashboard(fallbackDashboard);
    setMoodLogs([]);
    setJournals([]);
    setJournal(null);
    setChat(null);
    setAuthUsername("");
    setAuthPassword("");
    setStatus("Session closed");
  }

  async function submitJournal(event: FormEvent) {
    event.preventDefault();
    setStatus("Analyzing reflections...");
    try {
      const result = await apiPost<JournalEntry>("/journals", {
        content: journalText,
        exam_context: "exam preparation"
      });
      setJournal(result);
      setJournalText("");
      await refreshData();
      setStatus("Reflections analyzed");
    } catch {
      setStatus("Error: Session expired or invalid journal length.");
    }
  }

  async function submitMood(event: FormEvent) {
    event.preventDefault();
    setStatus("Saving log...");
    try {
      await apiPost("/mood-logs", {
        mood_score: moodScore,
        stress_level: stressLevel,
        sleep_hours: sleepHours,
        study_hours: studyHours,
        note: moodNote.trim() || undefined
      });
      setMoodNote("");
      await refreshData();
      setStatus("Log completed");
    } catch {
      setStatus("Failed to complete mood log.");
    }
  }

  async function submitChat(event: FormEvent) {
    event.preventDefault();
    setStatus("Thinking...");
    try {
      setChat(await apiPost<ChatResponse>("/chat", { message: chatText }));
      setChatText("");
      setStatus("Replied");
    } catch {
      setStatus("Chat session failed.");
    }
  }

  async function handleLoadMockData() {
    setStatus("Seeding wellness history logs...");
    try {
      const mockLogs = [
        { mood_score: 8, stress_level: 3, sleep_hours: 8.0, study_hours: 4.0, note: "Good rest. Prepared test revision." },
        { mood_score: 7, stress_level: 4, sleep_hours: 7.5, study_hours: 5.5, note: "Completed logic mock chapters." },
        { mood_score: 6, stress_level: 5, sleep_hours: 7.0, study_hours: 6.0, note: "Test scores published. Standard comparison pressure." },
        { mood_score: 5, stress_level: 7, sleep_hours: 6.0, study_hours: 8.0, note: "Studying physics late. Heavy anxiety." },
        { mood_score: 5, stress_level: 6, sleep_hours: 6.5, study_hours: 7.5, note: "Struggling with focus loops." },
        { mood_score: 6, stress_level: 5, sleep_hours: 7.5, study_hours: 6.0, note: "Breathing breaks helped stabilize energy." },
        { mood_score: 4, stress_level: 8, sleep_hours: 5.0, study_hours: 9.0, note: "Slept poorly, studied late. Feeling overwhelmed." }
      ];

      for (const log of mockLogs) {
        await apiPost("/mood-logs", log);
      }

      await apiPost("/journals", {
        content: "I studied UPSC topics for 9 hours today and slept only 5 hours. Everyone else seems so far ahead in test revisions. I feel guilty, exhausted, and incredibly anxious about the upcoming exam.",
        exam_context: "UPSC preparation"
      });

      setStatus("Mock logs populated!");
      await refreshData();
    } catch (err) {
      console.error(err);
      setStatus("Failed seeding data.");
    }
  }

  // Formatting chart data
  const chartData = useMemo(() => {
    return moodLogs.map((log) => {
      const date = new Date(log.created_at);
      const dayLabel = date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
      return {
        day: dayLabel,
        Mood: log.mood_score,
        Stress: log.stress_level ?? 0,
        Sleep: log.sleep_hours ?? 0,
        Study: log.study_hours ?? 0,
      };
    });
  }, [moodLogs]);

  // Auth Screen Render
  if (mounted && !token) {
    return (
      <main className="app-shell" style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "90vh" }}>
        <div className="panel" style={{ width: "100%", maxWidth: "420px", padding: "2.25rem", display: "grid", gap: "1.5rem" }}>
          <div style={{ textAlign: "center" }}>
            <span className="pill">MindMate AI</span>
            <h1 style={{ fontSize: "1.8rem", marginTop: "0.5rem" }}>Student Wellness Space</h1>
            <p className="muted" style={{ marginTop: "0.25rem" }}>A private, secure dashboard to manage mock test anxieties and prevent study burnout.</p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
            <button 
              type="button" 
              className={authView === "login" ? "" : "secondary"} 
              onClick={() => { setAuthView("login"); setAuthError(null); }}
            >
              🔑 Log In
            </button>
            <button 
              type="button" 
              className={authView === "signup" ? "" : "secondary"} 
              onClick={() => { setAuthView("signup"); setAuthError(null); }}
            >
              📝 Sign Up
            </button>
          </div>

          <form onSubmit={authView === "login" ? handleLogin : handleSignup} className="stack">
            <label htmlFor="username-input">
              Username
              <input
                id="username-input"
                type="text"
                value={authUsername}
                onChange={(e) => setAuthUsername(e.target.value)}
                placeholder="Unique username"
                required
                minLength={3}
              />
            </label>

            <label htmlFor="password-input">
              Password
              <input
                id="password-input"
                type="password"
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                placeholder="At least 6 characters"
                required
                minLength={6}
              />
            </label>

            {authError && (
              <div className="panel danger-text" style={{ borderColor: "var(--danger)", background: "rgba(220, 38, 38, 0.05)", padding: "0.75rem", fontSize: "0.9rem" }}>
                ⚠️ {authError}
              </div>
            )}

            <button type="submit" style={{ marginTop: "0.5rem" }}>
              {authView === "login" ? "Enter Dashboard" : "Register & Start"}
            </button>
          </form>

          <aside style={{ textAlign: "center", fontSize: "0.8rem" }} className="muted">
            Status: {status}
          </aside>
        </div>
      </main>
    );
  }

  // Dashboard Render (Authenticated)
  return (
    <main className="app-shell">
      {/* Accessibility Floating Panel */}
      <section className="settings-panel" aria-label="Accessibility & Preferences">
        <div className="settings-group">
          <span className="pill">Student: <strong>{username}</strong></span>
          <button 
            type="button" 
            className="settings-btn"
            style={{ borderColor: "var(--danger)", color: "var(--danger)" }}
            onClick={handleLogout}
            aria-label="Log out of account"
          >
            🚪 Log Out
          </button>
        </div>
        <div className="settings-group">
          <button 
            type="button" 
            className={`settings-btn ${darkMode ? "active" : ""}`}
            onClick={() => setDarkMode(!darkMode)}
            aria-label="Toggle Dark Mode"
          >
            {darkMode ? "☀️ Light" : "🌙 Dark"}
          </button>
          
          <button 
            type="button" 
            className={`settings-btn ${highContrast ? "active" : ""}`}
            onClick={() => setHighContrast(!highContrast)}
            aria-label="Toggle High Contrast Mode"
          >
            👁️ Contrast
          </button>
          
          <button 
            type="button" 
            className={`settings-btn ${dyslexiaFont ? "active" : ""}`}
            onClick={() => setDyslexiaFont(!dyslexiaFont)}
            aria-label="Toggle Dyslexia Font"
          >
            🔤 Dyslexic font
          </button>
        </div>
        
        <div className="settings-group">
          <span className="muted">Font size:</span>
          <button type="button" className={`settings-btn ${fontScale === 0.9 ? "active" : ""}`} onClick={() => setFontScale(0.9)} aria-label="Small text">S</button>
          <button type="button" className={`settings-btn ${fontScale === 1.0 ? "active" : ""}`} onClick={() => setFontScale(1.0)} aria-label="Medium text">M</button>
          <button type="button" className={`settings-btn ${fontScale === 1.15 ? "active" : ""}`} onClick={() => setFontScale(1.15)} aria-label="Large text">L</button>
          <button type="button" className={`settings-btn ${fontScale === 1.3 ? "active" : ""}`} onClick={() => setFontScale(1.3)} aria-label="Extra large text">XL</button>
        </div>
      </section>

      {/* Hero Header */}
      <section className="hero">
        <span className="pill">GenAI Wellness Companion</span>
        <h1>MindMate AI</h1>
        <p>
          Reflect honestly on exam pressures, track daily sleep-study balances, discover stress triggers,
          and receive personalized wellness next-steps.
        </p>
        <div style={{ marginTop: "0.5rem" }}>
          <button type="button" className="secondary" onClick={handleLoadMockData}>
            📥 Seed 7 Days of Mock Data
          </button>
        </div>
      </section>

      {/* Wellness Dashboard Summary Cards */}
      <section className="grid" aria-label="Wellness metrics overview">
        <article className="panel span-4 metric-card">
          <p className="metric-label">Mood Average</p>
          <p className="metric" aria-live="polite">
            {dashboard.mood_average > 0 ? `${dashboard.mood_average}/10` : "--"}
          </p>
        </article>
        
        <article className="panel span-4 metric-card">
          <p className="metric-label">Journal Streak</p>
          <p className="metric" aria-live="polite">
            {dashboard.journal_streak} {dashboard.journal_streak === 1 ? "day" : "days"}
          </p>
        </article>
        
        <article className="panel span-4 metric-card">
          <p className="metric-label">Burnout Risk Status</p>
          <p 
            className={`metric ${dashboard.burnout_risk !== "low" ? "danger" : ""}`}
            aria-live="polite"
          >
            {riskLabel}
          </p>
        </article>
      </section>

      {/* Main Feature Layout */}
      <section className="grid">
        {/* Left Column: Journal & Chat */}
        <div className="span-8 stack">
          {/* Daily Journal Form */}
          <form className="panel stack" onSubmit={submitJournal}>
            <div>
              <h2>Reflective Journal Entry</h2>
              <p className="muted">Reflect honestly on your mock results and study hours. MindMate parses emotions, stress triggers, and cognitive patterns.</p>
            </div>
            
            <label htmlFor="journal-textarea">
              Write here...
            </label>
            <textarea
              id="journal-textarea"
              rows={8}
              minLength={10}
              value={journalText}
              onChange={(e) => setJournalText(e.target.value)}
              placeholder="I studied JEE math for 9 hours today and slept only 5 hours. Everyone else seems ahead..."
              required
            />
            
            <button type="submit">Analyze Journal</button>
          </form>

          {/* AI Analysis Panel */}
          <section className="panel stack" aria-live="polite">
            <h2>Latest Stress-Pattern Insights</h2>
            {journal ? (
              <div className="stack" style={{ gap: "1.25rem" }}>
                <div className="flex-row">
                  <span className="pill">Primary Emotion: <strong>{journal.analysis.primary_emotion}</strong></span>
                  {journal.analysis.secondary_emotion && (
                    <span className="pill purple">Secondary: <strong>{journal.analysis.secondary_emotion}</strong></span>
                  )}
                  <span className="pill">Intensity: <strong>{journal.analysis.emotional_intensity}/10</strong></span>
                  <span className="pill">Risk Level: <strong>{journal.analysis.risk_level.toUpperCase()}</strong></span>
                </div>
                
                {journal.analysis.crisis_detected && (
                  <div className="panel danger-text" style={{ borderColor: "var(--danger)", background: "rgba(220, 38, 38, 0.05)" }}>
                    ⚠️ {journal.analysis.crisis_message}
                  </div>
                )}
                
                <div>
                  <h3>Triggers Detected</h3>
                  <div className="flex-row" style={{ marginTop: "0.25rem" }}>
                    {journal.analysis.triggers.map((trig) => (
                      <span key={trig} className="pill" style={{ fontSize: "0.8rem" }}>{trig}</span>
                    ))}
                  </div>
                </div>

                <div>
                  <h3>Cognitive Distortions</h3>
                  <ul style={{ margin: "0.25rem 0 0 1.25rem", padding: 0 }}>
                    {journal.analysis.thought_patterns.map((pattern) => (
                      <li key={pattern} className="muted">{pattern}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3>Empathetic Coping Actions</h3>
                  <ul style={{ margin: "0.25rem 0 0 1.25rem", padding: 0 }}>
                    {journal.analysis.coping_strategies.map((strategy) => (
                      <li key={strategy} style={{ fontWeight: 600, color: "var(--accent)" }}>{strategy}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <p className="muted">Your stress and emotional pattern analysis will display here after submitting a journal.</p>
            )}
          </section>

          {/* Empathetic Chat Companion */}
          <form className="panel stack" onSubmit={submitChat}>
            <div>
              <h2>Companion Chatbot</h2>
              <p className="muted">Talk to MindMate about your study blocks, score comparisons, or exhaustion.</p>
            </div>
            
            <label htmlFor="chat-textarea">Message MindMate</label>
            <textarea
              id="chat-textarea"
              rows={4}
              value={chatText}
              onChange={(e) => setChatText(e.target.value)}
              placeholder="I feel exhausted and I want to quit studying..."
              required
            />
            
            <button type="submit" className="accent-purple">Send Message</button>
            
            {chat && (
              <div className="panel stack" aria-live="polite" style={{ background: chat.crisis_detected ? "rgba(220, 38, 38, 0.05)" : "var(--accent-soft)", borderColor: chat.crisis_detected ? "var(--danger)" : "var(--card-border)" }}>
                <p style={{ fontWeight: 500 }}>{chat.response}</p>
                {chat.suggested_action && (
                  <p className="muted">
                    <strong>Suggested next-step:</strong> {chat.suggested_action}
                  </p>
                )}
              </div>
            )}
          </form>
        </div>

        {/* Right Column: Mood Logging, Insights, Mindfulness, Recharts */}
        <div className="span-4 stack">
          {/* Mood Log Form */}
          <form className="panel stack" onSubmit={submitMood}>
            <h2>Daily Mood Log</h2>
            
            <div className="range-display">
              <label htmlFor="mood-score-input">Mood average: {moodScore}</label>
            </div>
            <input 
              id="mood-score-input"
              type="range" 
              min="1" 
              max="10" 
              value={moodScore} 
              onChange={(e) => setMoodScore(Number(e.target.value))} 
            />

            <div className="range-display">
              <label htmlFor="stress-level-input">Stress index: {stressLevel}</label>
            </div>
            <input 
              id="stress-level-input"
              type="range" 
              min="1" 
              max="10" 
              value={stressLevel} 
              onChange={(e) => setStressLevel(Number(e.target.value))} 
            />

            <div className="row">
              <div>
                <label htmlFor="sleep-hours-input">Sleep hours</label>
                <input 
                  id="sleep-hours-input"
                  type="number" 
                  min="0" 
                  max="24" 
                  step="0.5"
                  value={sleepHours} 
                  onChange={(e) => setSleepHours(Number(e.target.value))} 
                />
              </div>
              <div>
                <label htmlFor="study-hours-input">Study hours</label>
                <input 
                  id="study-hours-input"
                  type="number" 
                  min="0" 
                  max="18" 
                  step="0.5"
                  value={studyHours} 
                  onChange={(e) => setStudyHours(Number(e.target.value))} 
                />
              </div>
            </div>

            <div>
              <label htmlFor="mood-note-input">Optional log note</label>
              <input 
                id="mood-note-input"
                type="text" 
                maxLength={100}
                placeholder="Any special event (e.g. mock exam)?" 
                value={moodNote}
                onChange={(e) => setMoodNote(e.target.value)}
              />
            </div>

            <button type="submit">Save Log</button>
          </form>

          {/* Weekly Insights Dashboard */}
          <section className="panel stack">
            <h2>Weekly Insights & Timeline</h2>
            <div className="stack" style={{ gap: "0.5rem" }}>
              {dashboard.insights.map((insight) => (
                <p key={insight} className="muted" style={{ paddingLeft: "0.5rem", borderLeft: "3px solid var(--accent)" }}>
                  {insight}
                </p>
              ))}
              <div style={{ marginTop: "0.5rem" }}>
                <p><strong>Goal Progress:</strong> {dashboard.wellness_progress}%</p>
              </div>
            </div>
          </section>

          {/* Adaptive Mindfulness exercises generator */}
          <section className="panel stack">
            <h2>Guided Mindfulness Exercises</h2>
            <p className="muted">Calm your nervous system dynamically.</p>
            <div className="flex-row">
              <button 
                type="button" 
                className={`settings-btn ${activeMindfulness === "breathing" ? "active" : ""}`}
                onClick={() => setActiveMindfulness(activeMindfulness === "breathing" ? null : "breathing")}
              >
                🌬️ 4-7-8 Breathing
              </button>
              
              <button 
                type="button" 
                className={`settings-btn ${activeMindfulness === "relaxation" ? "active" : ""}`}
                onClick={() => setActiveMindfulness(activeMindfulness === "relaxation" ? null : "relaxation")}
              >
                💤 Sleep Muscle Relaxation
              </button>

              <button 
                type="button" 
                className={`settings-btn ${activeMindfulness === "compassion" ? "active" : ""}`}
                onClick={() => setActiveMindfulness(activeMindfulness === "compassion" ? null : "compassion")}
              >
                ❤️ Compassion
              </button>
            </div>

            <div aria-live="polite">
              {activeMindfulness === "breathing" && (
                <div className="breathing-circle-container">
                  <div className="breathing-circle">
                    <span>{breathingPhase}<br/>{breathingSeconds}s</span>
                  </div>
                  <p className="muted" style={{ marginTop: "1rem", textAlign: "center", fontStyle: "italic" }}>
                    {breathingPhase === "Inhale" && "Breath in slowly through your nose..."}
                    {breathingPhase === "Hold" && "Hold your breath, stay present..."}
                    {breathingPhase === "Exhale" && "Exhale completely through your mouth..."}
                  </p>
                </div>
              )}

              {activeMindfulness === "relaxation" && (
                <div className="stack" style={{ gap: "0.5rem", padding: "0.5rem" }}>
                  <p><strong>Bedtime progressive muscle relaxation:</strong></p>
                  <p className="muted">1. Lie flat on your back, eyes closed.</p>
                  <p className="muted">2. Tense your toes for 5s, then let go completely.</p>
                  <p className="muted">3. Work up: calves, thighs, stomach, shoulders, face.</p>
                  <p className="muted">4. Breathe naturally and feel the heavy relaxation.</p>
                </div>
              )}

              {activeMindfulness === "compassion" && (
                <div className="stack" style={{ gap: "0.5rem", padding: "0.5rem" }}>
                  <p><strong>Self-Compassion Prompt:</strong></p>
                  <p className="muted">Reflect on your exam journey. Imagine a close friend was feeling this exhausted and anxious. What kind, encouraging words would you say to them? Can you write those exact same words to yourself today?</p>
                </div>
              )}
            </div>
          </section>

          {/* System Status Tracker */}
          <aside className="panel">
            <h3>System status</h3>
            <p className="muted" aria-live="polite">{status}</p>
          </aside>
        </div>
      </section>

      {/* Visual Analytics Graphs (Recharts) */}
      {mounted && chartData.length > 0 && (
        <section className="grid">
          {/* Mood & Stress History Line Chart */}
          <article className="panel span-6 stack">
            <h2>Mood & Stress Trend Lines</h2>
            <p className="muted">Daily correlation between your overall mood average and logged stress level.</p>
            <div style={{ width: "100%", height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={chartData}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorMood" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="var(--accent)" stopOpacity={0.0}/>
                    </linearGradient>
                    <linearGradient id="colorStress" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--purple)" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="var(--purple)" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                  <XAxis dataKey="day" stroke="var(--muted)" />
                  <YAxis domain={[1, 10]} stroke="var(--muted)" />
                  <Tooltip contentStyle={{ background: "var(--card-bg)", borderColor: "var(--card-border)", borderRadius: "10px" }} />
                  <Legend />
                  <Area type="monotone" dataKey="Mood" stroke="var(--accent)" strokeWidth={2} fillOpacity={1} fill="url(#colorMood)" />
                  <Area type="monotone" dataKey="Stress" stroke="var(--purple)" strokeWidth={2} fillOpacity={1} fill="url(#colorStress)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </article>

          {/* Sleep & Study Correlation Bar Chart */}
          <article className="panel span-6 stack">
            <h2>Sleep & Study Correlation</h2>
            <p className="muted">Track how study habits directly impact sleep hours.</p>
            <div style={{ width: "100%", height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartData}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                  <XAxis dataKey="day" stroke="var(--muted)" />
                  <YAxis stroke="var(--muted)" />
                  <Tooltip contentStyle={{ background: "var(--card-bg)", borderColor: "var(--card-border)", borderRadius: "10px" }} />
                  <Legend />
                  <Bar dataKey="Study" name="Study Hours" fill="var(--accent)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Sleep" name="Sleep Hours" fill="var(--purple)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </article>
        </section>
      )}
    </main>
  );
}
