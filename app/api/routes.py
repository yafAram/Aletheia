from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.api.schemas import (
    AletheiaSelfResetResponse,
    AletheiaSelfResponse,
    BondEventsResponse,
    BondResetResponse,
    BondStateResponse,
    ChatRequest,
    ChatResponse,
    EmotionStateResponse,
    InitiativeActionsResponse,
    InitiativeResetResponse,
    InitiativeAutonomyRequest,
    GoalCreateRequest,
    GoalListResponse,
    GoalResponse,
    InitiativeStateResponse,
    InitiativeUseActionRequest,
    InitiativeUseActionResponse,
    MemoryClearResponse,
    MemoryListResponse,
    PerceptionRequest,
    PerceptionResponse,
    PersonalityResetResponse,
    PersonalityStateResponse,
    RelationshipListResponse,
    SignificantMemoryListResponse,
    SttResponse,
    TtsRequest,
    TtsResponse,
    VoiceChatResponse,
    VoiceChatTtsResponse,
)
from app.application.chat_use_case import ChatUseCase
from app.core.config import Settings, get_settings
from app.domain.contracts import MemoryRepository
from app.infrastructure.aletheia_self_store import AletheiaSelfStore
from app.infrastructure.audio_store import AudioStore
from app.infrastructure.initiative_store import InitiativeStore
from app.infrastructure.goal_store import GoalStore
from app.infrastructure.ollama_client import OllamaClient
from app.infrastructure.ollama_embedding_client import OllamaEmbeddingClient
from app.infrastructure.personality_store import PersonalityStore
from app.infrastructure.relationship_store import RelationshipStore
from app.modules.aletheia_self_engine import AletheiaSelfEngine
from app.modules.emotion_engine import EmotionEngine
from app.modules.initiative_engine import InitiativeEngine
from app.modules.goal_engine import GoalEngine
from app.modules.personality_engine import PersonalityEngine
from app.modules.relationship_engine import RelationshipEngine


router = APIRouter(prefix="/api", tags=["Aletheia"])

_memory_repository: MemoryRepository | None = None

_emotion_engine = EmotionEngine()

_personality_store = PersonalityStore()
_personality_engine = PersonalityEngine(profile=_personality_store.load())

_aletheia_self_store = AletheiaSelfStore()
_aletheia_self_engine = _aletheia_self_store.load_engine()

_relationship_store = RelationshipStore()
_relationship_engine = _relationship_store.load_engine()

_initiative_store = InitiativeStore()
_initiative_engine = _initiative_store.load_engine()

_goal_store = GoalStore(path=get_settings().goal_state_path)
_goal_engine = _goal_store.load_engine()

_audio_store = AudioStore()
_stt_engine: VoskSttEngine | None = None
_tts_engine: PiperTtsEngine | None = None


def get_memory_repository(
    settings: Settings = Depends(get_settings),
) -> MemoryRepository:
    global _memory_repository

    if _memory_repository is None:
        # Import the vector backend only when memory is first requested. This keeps
        # health checks and non-memory routes independent of optional infrastructure.
        from app.infrastructure.qdrant_memory import QdrantMemoryRepository

        embedding_gateway = OllamaEmbeddingClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
        )

        _memory_repository = QdrantMemoryRepository(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            embedding_gateway=embedding_gateway,
            vector_size=settings.qdrant_vector_size,
        )

    return _memory_repository


def get_audio_store() -> AudioStore:
    return _audio_store


def get_stt_engine(
    settings: Settings = Depends(get_settings),
) -> VoskSttEngine:
    global _stt_engine

    if _stt_engine is None:
        from app.modules.stt_engine import VoskSttEngine

        _stt_engine = VoskSttEngine(
            model_path=settings.vosk_model_path,
            sample_rate=settings.stt_sample_rate,
        )

    return _stt_engine


def get_tts_engine(
    settings: Settings = Depends(get_settings),
) -> PiperTtsEngine:
    global _tts_engine

    if _tts_engine is None:
        from app.modules.tts_engine import PiperTtsEngine

        _tts_engine = PiperTtsEngine(
            model_path=settings.piper_model_path,
            config_path=settings.piper_config_path,
            output_dir=settings.tts_output_dir,
        )

    return _tts_engine


def get_emotion_engine() -> EmotionEngine:
    return _emotion_engine


def get_personality_store() -> PersonalityStore:
    return _personality_store


def get_personality_engine() -> PersonalityEngine:
    return _personality_engine


def get_aletheia_self_store() -> AletheiaSelfStore:
    return _aletheia_self_store


def get_aletheia_self_engine() -> AletheiaSelfEngine:
    return _aletheia_self_engine


def get_relationship_store() -> RelationshipStore:
    return _relationship_store


def get_relationship_engine() -> RelationshipEngine:
    return _relationship_engine


def get_initiative_store() -> InitiativeStore:
    return _initiative_store


def get_initiative_engine() -> InitiativeEngine:
    return _initiative_engine


def get_goal_store() -> GoalStore:
    return _goal_store


def get_goal_engine() -> GoalEngine:
    return _goal_engine


def get_chat_use_case(
    settings: Settings = Depends(get_settings),
    memory: MemoryRepository = Depends(get_memory_repository),
    emotion_engine: EmotionEngine = Depends(get_emotion_engine),
    personality_engine: PersonalityEngine = Depends(get_personality_engine),
    personality_store: PersonalityStore = Depends(get_personality_store),
    aletheia_self_engine: AletheiaSelfEngine = Depends(get_aletheia_self_engine),
    aletheia_self_store: AletheiaSelfStore = Depends(get_aletheia_self_store),
    relationship_engine: RelationshipEngine = Depends(get_relationship_engine),
    relationship_store: RelationshipStore = Depends(get_relationship_store),
    initiative_engine: InitiativeEngine = Depends(get_initiative_engine),
    initiative_store: InitiativeStore = Depends(get_initiative_store),
    goal_engine: GoalEngine = Depends(get_goal_engine),
    goal_store: GoalStore = Depends(get_goal_store),
) -> ChatUseCase:
    llm = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        num_predict=settings.ollama_num_predict,
        temperature=settings.ollama_temperature,
        top_p=settings.ollama_top_p,
        num_ctx=settings.ollama_num_ctx,
        keep_alive=settings.ollama_keep_alive,
    )

    return ChatUseCase(
        llm=llm,
        memory=memory,
        emotion_engine=emotion_engine,
        personality_engine=personality_engine,
        personality_store=personality_store,
        aletheia_self_engine=aletheia_self_engine,
        aletheia_self_store=aletheia_self_store,
        relationship_engine=relationship_engine,
        relationship_store=relationship_store,
        initiative_engine=initiative_engine,
        initiative_store=initiative_store,
        goal_engine=goal_engine,
        goal_store=goal_store,
        memory_search_limit=settings.memory_search_limit,
        significant_memory_prompt_limit=settings.significant_memory_prompt_limit,
        bond_event_prompt_limit=settings.bond_event_prompt_limit,
        initiative_action_prompt_limit=settings.initiative_action_prompt_limit,
        goal_prompt_limit=settings.goal_prompt_limit,
        async_memory_persistence=settings.async_memory_persistence,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
    use_case: ChatUseCase = Depends(get_chat_use_case),
) -> ChatResponse:
    result = await use_case.execute(
        message=request.message,
        use_memory=request.use_memory,
    )

    return ChatResponse(
        response=result.response,
        model=settings.ollama_model,
        latency_ms=result.latency_ms,
        memory_items=result.memory_items,
        emotion_state=result.emotion_state,
        personality_state=result.personality_state,
        self_state=result.self_state,
        relationship_state=result.relationship_state,
        significant_memory_count=result.significant_memory_count,
        bond_state=result.bond_state,
        bond_event_count=result.bond_event_count,
        initiative_state=result.initiative_state,
        initiative_action_count=result.initiative_action_count,
    )


@router.get("/memory", response_model=MemoryListResponse)
async def list_memory(
    limit: int = Query(default=20, ge=1, le=100),
    memory: MemoryRepository = Depends(get_memory_repository),
) -> MemoryListResponse:
    items = await memory.list_items(limit=limit)
    total = await memory.count()

    return MemoryListResponse(items=items, total=total)


@router.delete("/memory", response_model=MemoryClearResponse)
async def clear_memory(
    memory: MemoryRepository = Depends(get_memory_repository),
) -> MemoryClearResponse:
    deleted_items = await memory.count()
    await memory.clear()

    return MemoryClearResponse(
        status="memory_cleared",
        deleted_items=deleted_items,
    )


@router.get("/emotion", response_model=EmotionStateResponse)
async def get_emotion_state(
    emotion_engine: EmotionEngine = Depends(get_emotion_engine),
) -> EmotionStateResponse:
    return EmotionStateResponse(**emotion_engine.state.as_dict())


@router.get("/personality", response_model=PersonalityStateResponse)
async def get_personality_state(
    personality_engine: PersonalityEngine = Depends(get_personality_engine),
) -> PersonalityStateResponse:
    return PersonalityStateResponse(**personality_engine.profile.as_dict())


@router.post("/personality/reset", response_model=PersonalityResetResponse)
async def reset_personality(
    personality_store: PersonalityStore = Depends(get_personality_store),
) -> PersonalityResetResponse:
    global _personality_engine

    profile = personality_store.reset()
    _personality_engine = PersonalityEngine(profile=profile)

    return PersonalityResetResponse(
        status="personality_reset",
        personality=PersonalityStateResponse(**profile.as_dict()),
    )


@router.get("/self", response_model=AletheiaSelfResponse)
async def get_aletheia_self(
    aletheia_self_engine: AletheiaSelfEngine = Depends(get_aletheia_self_engine),
    relationship_engine: RelationshipEngine = Depends(get_relationship_engine),
) -> AletheiaSelfResponse:
    state = aletheia_self_engine.as_dict()
    state["relationships"] = {
        key: bond.as_dict()
        for key, bond in relationship_engine.bonds.items()
    }
    return AletheiaSelfResponse(**state)


@router.get("/relationships", response_model=RelationshipListResponse)
async def get_relationships(
    relationship_engine: RelationshipEngine = Depends(get_relationship_engine),
) -> RelationshipListResponse:
    relationships = {
        key: bond.as_dict()
        for key, bond in relationship_engine.bonds.items()
    }

    return RelationshipListResponse(
        relationships=relationships,
        total=len(relationships),
    )


@router.get("/significant-memories", response_model=SignificantMemoryListResponse)
async def get_significant_memories(
    aletheia_self_engine: AletheiaSelfEngine = Depends(get_aletheia_self_engine),
) -> SignificantMemoryListResponse:
    items = [
        memory.as_dict()
        for memory in aletheia_self_engine.significant_memories
    ]

    return SignificantMemoryListResponse(
        items=items,
        total=len(items),
    )


@router.post("/self/reset", response_model=AletheiaSelfResetResponse)
async def reset_aletheia_self(
    aletheia_self_store: AletheiaSelfStore = Depends(get_aletheia_self_store),
    relationship_engine: RelationshipEngine = Depends(get_relationship_engine),
) -> AletheiaSelfResetResponse:
    global _aletheia_self_engine

    _aletheia_self_engine = aletheia_self_store.reset()

    state = _aletheia_self_engine.as_dict()
    state["relationships"] = {
        key: bond.as_dict()
        for key, bond in relationship_engine.bonds.items()
    }
    return AletheiaSelfResetResponse(
        status="self_reset",
        state=AletheiaSelfResponse(**state),
    )


@router.get("/bond", response_model=BondStateResponse)
async def get_bond_state(
    relationship_engine: RelationshipEngine = Depends(get_relationship_engine),
) -> BondStateResponse:
    return BondStateResponse(**relationship_engine.as_dict())


@router.get("/bond/events", response_model=BondEventsResponse)
async def get_bond_events(
    relationship_engine: RelationshipEngine = Depends(get_relationship_engine),
) -> BondEventsResponse:
    items = [
        event.as_dict()
        for event in relationship_engine.events
    ]

    return BondEventsResponse(
        items=items,
        total=len(items),
    )


@router.post("/bond/reset", response_model=BondResetResponse)
async def reset_bond_state(
    relationship_store: RelationshipStore = Depends(get_relationship_store),
) -> BondResetResponse:
    global _relationship_engine

    _relationship_engine = relationship_store.reset()

    return BondResetResponse(
        status="bond_reset",
        state=BondStateResponse(**_relationship_engine.as_dict()),
    )


@router.post("/perception", response_model=PerceptionResponse)
async def register_perception(
    request: PerceptionRequest,
    initiative_engine: InitiativeEngine = Depends(get_initiative_engine),
    initiative_store: InitiativeStore = Depends(get_initiative_store),
) -> PerceptionResponse:
    action = initiative_engine.register_observation(
        source=request.source,
        text_observation=request.text_observation,
        facial_expression=request.facial_expression,
        vocal_tone=request.vocal_tone,
        detected_mood=request.detected_mood,
        energy_level=request.energy_level,
        stress_level=request.stress_level,
        engagement_level=request.engagement_level,
        confidence=request.confidence,
    )

    initiative_store.save_engine(initiative_engine)

    observation = initiative_engine.observations[-1].as_dict()

    return PerceptionResponse(
        observation=observation,
        generated_action=action.as_dict() if action else None,
        initiative_state=initiative_engine.state.as_dict(),
    )


@router.get("/initiative", response_model=InitiativeStateResponse)
async def get_initiative_state(
    initiative_engine: InitiativeEngine = Depends(get_initiative_engine),
) -> InitiativeStateResponse:
    data = initiative_engine.as_dict()

    return InitiativeStateResponse(
        state=data["state"],
        observations=data["observations"],
        actions=data["actions"],
    )


@router.get("/initiative/actions", response_model=InitiativeActionsResponse)
async def get_initiative_actions(
    initiative_engine: InitiativeEngine = Depends(get_initiative_engine),
) -> InitiativeActionsResponse:
    actions = [
        action.as_dict()
        for action in initiative_engine.actions
    ]

    return InitiativeActionsResponse(
        items=actions,
        total=len(actions),
    )


@router.post("/initiative/use", response_model=InitiativeUseActionResponse)
async def use_initiative_action(
    request: InitiativeUseActionRequest,
    initiative_engine: InitiativeEngine = Depends(get_initiative_engine),
    initiative_store: InitiativeStore = Depends(get_initiative_store),
) -> InitiativeUseActionResponse:
    action = initiative_engine.mark_action_used(action_id=request.action_id)
    initiative_store.save_engine(initiative_engine)

    return InitiativeUseActionResponse(
        status="action_used" if action else "no_action_found",
        action=action.as_dict() if action else None,
        state=initiative_engine.state.as_dict(),
    )


@router.post("/initiative/reset", response_model=InitiativeResetResponse)
async def reset_initiative(
    initiative_store: InitiativeStore = Depends(get_initiative_store),
) -> InitiativeResetResponse:
    _initiative_engine.reset()
    initiative_store.save_engine(_initiative_engine)
    data = _initiative_engine.as_dict()

    return InitiativeResetResponse(
        status="initiative_reset",
        state=InitiativeStateResponse(
            state=data["state"],
            observations=data["observations"],
            actions=data["actions"],
        ),
    )


@router.get("/initiative/pending", response_model=InitiativeActionsResponse)
async def get_pending_initiatives(
    settings: Settings = Depends(get_settings),
    initiative_engine: InitiativeEngine = Depends(get_initiative_engine),
) -> InitiativeActionsResponse:
    actions = [
        action.as_dict()
        for action in initiative_engine.pending_autonomous_actions(
            limit=settings.initiative_max_pending_actions
        )
    ]
    return InitiativeActionsResponse(items=actions, total=len(actions))


@router.post("/initiative/autonomy", response_model=InitiativeStateResponse)
async def set_initiative_autonomy(
    request: InitiativeAutonomyRequest,
    initiative_engine: InitiativeEngine = Depends(get_initiative_engine),
    initiative_store: InitiativeStore = Depends(get_initiative_store),
) -> InitiativeStateResponse:
    initiative_engine.state.autonomy_enabled = request.enabled
    initiative_store.save_engine(initiative_engine)
    data = initiative_engine.as_dict()
    return InitiativeStateResponse(
        state=data["state"],
        observations=data["observations"],
        actions=data["actions"],
    )


@router.post("/initiative/{action_id}/delivered", response_model=InitiativeUseActionResponse)
async def mark_initiative_delivered(
    action_id: str,
    initiative_engine: InitiativeEngine = Depends(get_initiative_engine),
    initiative_store: InitiativeStore = Depends(get_initiative_store),
) -> InitiativeUseActionResponse:
    action = initiative_engine.mark_action_delivered(action_id)
    if action is not None:
        initiative_store.save_engine(initiative_engine)
    return InitiativeUseActionResponse(
        status="delivered" if action else "no_action_found",
        action=action.as_dict() if action else None,
        state=initiative_engine.state.as_dict(),
    )


@router.post("/initiative/{action_id}/dismiss", response_model=InitiativeUseActionResponse)
async def dismiss_initiative(
    action_id: str,
    initiative_engine: InitiativeEngine = Depends(get_initiative_engine),
    initiative_store: InitiativeStore = Depends(get_initiative_store),
) -> InitiativeUseActionResponse:
    action = initiative_engine.dismiss_action(action_id)
    if action is not None:
        initiative_store.save_engine(initiative_engine)
    return InitiativeUseActionResponse(
        status="dismissed" if action else "no_action_found",
        action=action.as_dict() if action else None,
        state=initiative_engine.state.as_dict(),
    )


@router.get("/goals", response_model=GoalListResponse)
async def get_goals(
    goal_engine: GoalEngine = Depends(get_goal_engine),
) -> GoalListResponse:
    items = [goal.as_dict() for goal in goal_engine.list_goals()]
    return GoalListResponse(items=items, total=len(items))


@router.post("/goals", response_model=GoalResponse)
async def create_goal(
    request: GoalCreateRequest,
    goal_engine: GoalEngine = Depends(get_goal_engine),
    goal_store: GoalStore = Depends(get_goal_store),
) -> GoalResponse:
    try:
        goal = goal_engine.add_goal(request.description, priority=request.priority)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    goal_store.save_engine(goal_engine)
    return GoalResponse(**goal.as_dict())


@router.post("/goals/{goal_id}/complete", response_model=GoalResponse)
async def complete_goal(
    goal_id: str,
    goal_engine: GoalEngine = Depends(get_goal_engine),
    goal_store: GoalStore = Depends(get_goal_store),
) -> GoalResponse:
    goal = goal_engine.complete_goal(goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found.")
    goal_store.save_engine(goal_engine)
    return GoalResponse(**goal.as_dict())


@router.post("/stt/transcribe", response_model=SttResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    audio_store: AudioStore = Depends(get_audio_store),
    stt_engine: VoskSttEngine = Depends(get_stt_engine),
) -> SttResponse:
    try:
        audio_path = await audio_store.save_upload(file)
        result = stt_engine.transcribe(audio_path)

        return SttResponse(
            text=result.text,
            confidence=result.confidence,
            duration_seconds=result.duration_seconds,
            words=result.words,
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/voice/chat", response_model=VoiceChatResponse)
async def voice_chat(
    file: UploadFile = File(...),
    use_memory: bool = True,
    settings: Settings = Depends(get_settings),
    audio_store: AudioStore = Depends(get_audio_store),
    stt_engine: VoskSttEngine = Depends(get_stt_engine),
    use_case: ChatUseCase = Depends(get_chat_use_case),
) -> VoiceChatResponse:
    try:
        audio_path = await audio_store.save_upload(file)
        transcription = stt_engine.transcribe(audio_path)

        if not transcription.text:
            raise HTTPException(
                status_code=400,
                detail="No speech was detected in the audio.",
            )

        result = await use_case.execute(
            message=transcription.text,
            use_memory=use_memory,
        )

        return VoiceChatResponse(
            transcription=SttResponse(
                text=transcription.text,
                confidence=transcription.confidence,
                duration_seconds=transcription.duration_seconds,
                words=transcription.words,
            ),
            response=result.response,
            model=settings.ollama_model,
            latency_ms=result.latency_ms,
            memory_items=result.memory_items,
            emotion_state=result.emotion_state,
            personality_state=result.personality_state,
            self_state=result.self_state,
            relationship_state=result.relationship_state,
            significant_memory_count=result.significant_memory_count,
            bond_state=result.bond_state,
            bond_event_count=result.bond_event_count,
            initiative_state=result.initiative_state,
            initiative_action_count=result.initiative_action_count,
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/tts/speak", response_model=TtsResponse)
async def speak_text(
    request: TtsRequest,
    tts_engine: PiperTtsEngine = Depends(get_tts_engine),
) -> TtsResponse:
    try:
        result = tts_engine.synthesize(
            text=request.text,
            emotion=request.emotion,
        )

        return TtsResponse(
            text=result.text,
            emotion=result.emotion,
            audio_url=f"/api/tts/audio/{result.filename}",
            filename=result.filename,
            voice_style=result.voice_style,
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/tts/audio/{filename}")
async def get_tts_audio(
    filename: str,
    settings: Settings = Depends(get_settings),
):
    # Only allow a plain filename; never let a URL path escape the TTS directory.
    if not filename or Path(filename).name != filename or filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid audio filename.")

    output_dir = Path(settings.tts_output_dir).resolve()
    audio_path = (output_dir / filename).resolve()
    if audio_path.parent != output_dir:
        raise HTTPException(status_code=400, detail="Invalid audio filename.")

    if not audio_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found.")

    return FileResponse(
        path=str(audio_path),
        media_type="audio/wav",
        filename=filename,
    )


@router.post("/voice/chat/tts", response_model=VoiceChatTtsResponse)
async def voice_chat_with_tts(
    file: UploadFile = File(...),
    use_memory: bool = True,
    settings: Settings = Depends(get_settings),
    audio_store: AudioStore = Depends(get_audio_store),
    stt_engine: VoskSttEngine = Depends(get_stt_engine),
    tts_engine: PiperTtsEngine = Depends(get_tts_engine),
    use_case: ChatUseCase = Depends(get_chat_use_case),
) -> VoiceChatTtsResponse:
    try:
        audio_path = await audio_store.save_upload(file)
        transcription = stt_engine.transcribe(audio_path)

        if not transcription.text:
            raise HTTPException(
                status_code=400,
                detail="No speech was detected in the audio.",
            )

        result = await use_case.execute(
            message=transcription.text,
            use_memory=use_memory,
        )

        tts_result = tts_engine.synthesize(
            text=result.response,
            emotion="auto",
            emotion_state=result.emotion_state,
        )

        return VoiceChatTtsResponse(
            transcription=SttResponse(
                text=transcription.text,
                confidence=transcription.confidence,
                duration_seconds=transcription.duration_seconds,
                words=transcription.words,
            ),
            response=result.response,
            audio_url=f"/api/tts/audio/{tts_result.filename}",
            audio_filename=tts_result.filename,
            tts_emotion=tts_result.emotion,
            voice_style=tts_result.voice_style,
            model=settings.ollama_model,
            latency_ms=result.latency_ms,
            memory_items=result.memory_items,
            emotion_state=result.emotion_state,
            personality_state=result.personality_state,
            self_state=result.self_state,
            relationship_state=result.relationship_state,
            significant_memory_count=result.significant_memory_count,
            bond_state=result.bond_state,
            bond_event_count=result.bond_event_count,
            initiative_state=result.initiative_state,
            initiative_action_count=result.initiative_action_count,
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error