export type RiskLevel = "low" | "moderate" | "high" | "crisis";

export type JournalAnalysis = {
  primary_emotion: string;
  secondary_emotion?: string | null;
  emotional_intensity: number;
  sentiment: string;
  triggers: string[];
  thought_patterns: string[];
  coping_strategies: string[];
  risk_level: RiskLevel;
  crisis_detected: boolean;
  crisis_message?: string | null;
};

export type JournalEntry = {
  id: string;
  content: string;
  created_at: string;
  analysis: JournalAnalysis;
};

export type DashboardSummary = {
  mood_average: number;
  journal_streak: number;
  burnout_risk: RiskLevel;
  wellness_progress: number;
  insights: string[];
  recent_emotions: string[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";


function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("mindmate-token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return headers;
}


export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const authHeaders = getAuthHeaders();
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders
    },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}


export async function apiGet<T>(path: string): Promise<T> {
  const authHeaders = getAuthHeaders();
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      ...authHeaders
    },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}
