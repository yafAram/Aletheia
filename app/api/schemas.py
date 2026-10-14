from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, examples=["Hola Aletheia"])
    use_memory: bool = Field(default=True)


class ChatResponse(BaseModel):
    response: str
    model: str
    latency_ms: int
    memory_items: int
    emotion_state: dict
    personality_state: dict
    self_state: dict
    relationship_state: dict
    significant_memory_count: int
    bond_state: dict
    bond_event_count: int
    initiative_state: dict
    initiative_action_count: int


class MemoryItemResponse(BaseModel):
    id: str
    text: str
    metadata: dict
    created_at: str


class MemoryListResponse(BaseModel):
    items: list[MemoryItemResponse]
    total: int


class MemoryClearResponse(BaseModel):
    status: str
    deleted_items: int


class EmotionStateResponse(BaseModel):
    mood: str
    affection: float
    trust: float
    stress: float
    curiosity: float
    energy: float


class PersonalityStateResponse(BaseModel):
    warmth: float
    curiosity: float
    playfulness: float
    empathy: float
    confidence: float
    independence: float
    tenderness: float
    spontaneity: float
    formality: float


class PersonalityResetResponse(BaseModel):
    status: str
    personality: PersonalityStateResponse


class AletheiaSelfResponse(BaseModel):
    self_model: dict
    relationships: dict
    significant_memories: list[dict]


class AletheiaSelfResetResponse(BaseModel):
    status: str
    state: AletheiaSelfResponse


class SignificantMemoryListResponse(BaseModel):
    items: list[dict]
    total: int


class RelationshipListResponse(BaseModel):
    relationships: dict
    total: int


class BondStateResponse(BaseModel):
    bonds: dict
    events: list[dict]


class BondResetResponse(BaseModel):
    status: str
    state: BondStateResponse


class BondEventsResponse(BaseModel):
    items: list[dict]
    total: int


class PerceptionRequest(BaseModel):
    source: str = Field(default="manual", examples=["visual", "audio", "chat", "system"])
    text_observation: str | None = None
    facial_expression: str | None = None
    vocal_tone: str | None = None
    detected_mood: str | None = None
    energy_level: float | None = Field(default=None, ge=0.0, le=1.0)
    stress_level: float | None = Field(default=None, ge=0.0, le=1.0)
    engagement_level: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence: float = Field(default=0.50, ge=0.0, le=1.0)


class PerceptionResponse(BaseModel):
    observation: dict
    generated_action: dict | None
    initiative_state: dict


class InitiativeStateResponse(BaseModel):
    state: dict
    observations: list[dict]
    actions: list[dict]


class InitiativeActionsResponse(BaseModel):
    items: list[dict]
    total: int


class InitiativeUseActionRequest(BaseModel):
    action_id: str | None = None


class InitiativeUseActionResponse(BaseModel):
    status: str
    action: dict | None
    state: dict


class InitiativeResetResponse(BaseModel):
    status: str
    state: InitiativeStateResponse


class SttResponse(BaseModel):
    text: str
    confidence: float
    duration_seconds: float
    words: list[dict]


class VoiceChatResponse(BaseModel):
    transcription: SttResponse
    response: str
    model: str
    latency_ms: int
    memory_items: int
    emotion_state: dict
    personality_state: dict
    self_state: dict
    relationship_state: dict
    significant_memory_count: int
    bond_state: dict
    bond_event_count: int
    initiative_state: dict
    initiative_action_count: int


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1)
    emotion: str = Field(default="auto")


class TtsResponse(BaseModel):
    text: str
    emotion: str
    audio_url: str
    filename: str
    voice_style: dict


class VoiceChatTtsResponse(BaseModel):
    transcription: SttResponse
    response: str
    audio_url: str
    audio_filename: str
    tts_emotion: str
    voice_style: dict
    model: str
    latency_ms: int
    memory_items: int
    emotion_state: dict
    personality_state: dict
    self_state: dict
    relationship_state: dict
    significant_memory_count: int
    bond_state: dict
    bond_event_count: int
    initiative_state: dict
    initiative_action_count: int


class InitiativeAutonomyRequest(BaseModel):
    enabled: bool


class GoalCreateRequest(BaseModel):
    description: str = Field(..., min_length=3, max_length=180)
    priority: float = Field(default=0.6, ge=0.0, le=1.0)


class GoalResponse(BaseModel):
    id: str
    description: str
    status: str
    source: str
    priority: float
    confidence: float
    created_at: str
    updated_at: str
    last_mentioned_at: str
    last_check_in_at: str | None = None


class GoalListResponse(BaseModel):
    items: list[GoalResponse]
    total: int
