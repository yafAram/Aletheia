# Arquitectura

Aletheia separa cliente, API, orquestación, motores de dominio y adaptadores externos. El agente de escritorio se ejecuta como proceso separado porque necesita la sesión gráfica del host.

~~~mermaid
flowchart TB
    WEB[React Web] --> API[FastAPI]
    ELECTRON[Electron / Lumina] --> API
    ELECTRON --> AGENT[Desktop Agent]
    API --> CHAT[ChatUseCase]
    CHAT --> PROMPT[PromptBuilder]
    CHAT --> DOMAIN[Domain Engines]
    DOMAIN --> STORES[JSON Stores]
    CHAT --> OLLAMA[OllamaClient]
    CHAT --> MEMORY[QdrantMemoryRepository]
    MEMORY --> EMB[OllamaEmbeddingClient]
    MEMORY --> Q[(Qdrant)]
    AGENT --> OS[Host OS]
~~~

## Backend
- app/api: rutas HTTP, dependencias y esquemas Pydantic.
- app/application: casos de uso y loop de iniciativa.
- app/domain: contratos, entidades y cognitive workspace.
- app/modules: motores de personalidad, emoción, objetivos, iniciativa, relaciones y estado propio; STT/TTS.
- app/infrastructure: Ollama, embeddings, Qdrant y persistencia local.
- app/core: configuración, eventos, bus, logging y normalización.

## Flujo de chat
1. API valida ChatRequest.
2. ChatUseCase recupera recuerdos si use_memory está activo.
3. Motores aportan estado y objetivos.
4. PromptBuilder construye el contexto.
5. OllamaClient genera respuesta.
6. Stores persisten estado y memoria según su configuración.

## Memoria
Qdrant almacena vectores y payload. Ollama genera embeddings. La colección requiere dimensión compatible con el modelo; el valor inicial es 768. Objetivos, iniciativa, personalidad, relaciones y estado propio se guardan en stores separados.

## Iniciativa
InitiativeAutonomyLoop se inicia y cancela con el lifespan de FastAPI. Evalúa inactividad, cooldown y límites. Las propuestas se pueden pausar, entregar o descartar. No ejecuta comandos generales.

## Desktop
Electron carga React con ?desktop=1 y utiliza preload/IPC limitado. El renderer tiene contextIsolation, nodeIntegration deshabilitado y sandbox. El agente autentica con Bearer token y ejecuta alias permitidos mediante subprocess sin shell.

## Límites
- API principal sin autenticación de usuario.
- Ollama/Qdrant/modelos son dependencias externas al proceso API.
- Voz requiere modelos locales.
- Captura es puntual; no existe visión continua.
- Algunas rutas del agente no están conectadas a la UI.
