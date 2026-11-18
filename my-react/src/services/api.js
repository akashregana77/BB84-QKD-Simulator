// API service for BB84 QKD Simulator
export const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

export async function sendQuantumChat(message, history = []) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || errorData.reply || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function analyzeSimulationState(state) {
  const response = await fetch(`${API_BASE}/api/analyze-state`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function askAnalysisQuestion(question, simulationState, previousAnalysis, history = []) {
  const response = await fetch(`${API_BASE}/api/analyze-question`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, simulationState, previousAnalysis, history }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || errorData.answer || `HTTP ${response.status}`);
  }
  return response.json();
}
