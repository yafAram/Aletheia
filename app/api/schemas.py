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