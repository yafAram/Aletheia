export type EmotionState = {
  mood?: string;
  affection?: number;
  trust?: number;
  stress?: number;
  curiosity?: number;
  energy?: number;
};

export type ChatResponse = {
  response: string;
  model: string;
  latency_ms: number;
  memory_items: number;
  emotion_state: EmotionState;
  personality_state: Record<string, unknown>;
  self_state: Record<string, unknown>;
  relationship_state: Record<string, unknown>;
  significant_memory_count: number;
  bond_state: Record<string, unknown>;
  bond_event_count: number;
  initiative_state: Record<string, unknown>;
  initiative_action_count: number;
};

export type TtsResponse = {
  text: string;
  emotion: string;
  audio_url: string;
  filename: string;
  voice_style: Record<string, unknown>;
};

export type AletheiaMood =
  | "idle"
  | "thinking"
  | "speaking"
  | "happy"
  | "warm"
  | "tired"
  | "stressed"
  | "curious";