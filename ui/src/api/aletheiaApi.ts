import type { ChatResponse, TtsResponse } from "../types";

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

export async function getEmotionState() {
  const response = await fetch(`${API_BASE_URL}/api/emotion`);

  if (!response.ok) {
    throw new Error("No se pudo consultar el estado emocional.");
  }

  return response.json();
}

export async function getInitiativeState() {
  const response = await fetch(`${API_BASE_URL}/api/initiative`);

  if (!response.ok) {
    throw new Error("No se pudo consultar la iniciativa.");
  }

  return response.json();
}