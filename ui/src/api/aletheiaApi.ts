import type {
  ChatResponse,
  EmotionState,
  Goal,
  GoalListResponse,
  InitiativeAction,
  InitiativeStateResponse,
  TtsResponse,
} from "../types";

const API_BASE_URL = "http://localhost:8000";

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      use_memory: true,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "No se pudo enviar el mensaje.");
  }

  return response.json();
}

export async function synthesizeSpeech(
  text: string,
  emotion: string = "auto"
): Promise<TtsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/tts/speak`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text,
      emotion,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "No se pudo generar la voz.");
  }

  return response.json();
}

export function buildAudioUrl(audioUrl: string): string {
  return `${API_BASE_URL}${audioUrl}`;
}

export async function getEmotionState(): Promise<EmotionState> {
  const response = await fetch(`${API_BASE_URL}/api/emotion`);

  if (!response.ok) {
    throw new Error("No se pudo consultar el estado emocional.");
  }

  return response.json();
}

export async function getInitiativeState(): Promise<InitiativeStateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/initiative`);

  if (!response.ok) {
    throw new Error("No se pudo consultar la iniciativa.");
  }

  return response.json();
}

export async function getPendingInitiatives(): Promise<{
  items: InitiativeAction[];
  total: number;
}> {
  const response = await fetch(`${API_BASE_URL}/api/initiative/pending`);
  if (!response.ok) throw new Error("No se pudieron consultar las iniciativas pendientes.");
  return response.json();
}

export async function markInitiativeDelivered(actionId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/initiative/${encodeURIComponent(actionId)}/delivered`,
    { method: "POST" }
  );
  if (!response.ok) throw new Error("No se pudo confirmar la iniciativa.");
}

export async function dismissInitiative(actionId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/initiative/${encodeURIComponent(actionId)}/dismiss`,
    { method: "POST" }
  );
  if (!response.ok) throw new Error("No se pudo descartar la iniciativa.");
}

export async function setInitiativeAutonomy(enabled: boolean): Promise<InitiativeStateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/initiative/autonomy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!response.ok) throw new Error("No se pudo actualizar la autonomía.");
  return response.json();
}

export async function getGoals(): Promise<GoalListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/goals`);
  if (!response.ok) throw new Error("No se pudieron consultar los objetivos.");
  return response.json();
}

export async function createGoal(description: string): Promise<Goal> {
  const response = await fetch(`${API_BASE_URL}/api/goals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description, priority: 0.6 }),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "No se pudo guardar el objetivo.");
  }
  return response.json();
}

export async function completeGoal(goalId: string): Promise<Goal> {
  const response = await fetch(`${API_BASE_URL}/api/goals/${encodeURIComponent(goalId)}/complete`, {
    method: "POST",
  });
  if (!response.ok) throw new Error("No se pudo completar el objetivo.");
  return response.json();
}
