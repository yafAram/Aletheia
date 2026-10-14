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

export type InitiativeAction = {
  id: string;
  type: string;
  priority: number;
  reason: string;
  suggested_message: string;
  should_interrupt: boolean;
  cooldown_seconds: number;
  created_at: string;
  origin: string;
  goal_id?: string | null;
  delivered_at?: string | null;
  dismissed_at?: string | null;
};

export type Goal = {
  id: string;
  description: string;
  status: string;
  source: string;
  priority: number;
  confidence: number;
  created_at: string;
  updated_at: string;
  last_mentioned_at: string;
  last_check_in_at?: string | null;
};

export type GoalListResponse = {
  items: Goal[];
  total: number;
};

export type InitiativeStateResponse = {
  state: Record<string, unknown> & { autonomy_enabled?: boolean };
  observations: Record<string, unknown>[];
  actions: InitiativeAction[];
};
