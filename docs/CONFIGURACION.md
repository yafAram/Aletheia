# Configuración

El backend lee variables de entorno y .env mediante Pydantic Settings. La fuente de campos es app/core/config.py y los valores de ejemplo están en .env.example.

| Variable | Default | Uso |
|---|---|---|
| APP_NAME | Aletheia Local MVP | Nombre API |
| APP_VERSION | 0.1.0 | Versión API |
| ENVIRONMENT | local | Entorno |
| LOG_LEVEL | INFO | Nivel de log |
| OLLAMA_BASE_URL | http://ollama:11434 | Ollama en Compose |
| OLLAMA_MODEL | llama3.2:3b | Modelo de chat |
| OLLAMA_EMBEDDING_MODEL | nomic-embed-text | Embeddings |
| QDRANT_URL | http://qdrant:6333 | Qdrant |
| QDRANT_COLLECTION | aletheia_memory | Colección |
| QDRANT_VECTOR_SIZE | 768 | Dimensión esperada |
| OLLAMA_NUM_PREDICT | 220 | Tokens de salida |
| OLLAMA_TEMPERATURE | 0.7 | Temperatura |
| OLLAMA_TOP_P | 0.9 | Top-p |
| OLLAMA_NUM_CTX | 3072 | Ventana contexto |
| OLLAMA_KEEP_ALIVE | 30m | Permanencia modelo |
| MEMORY_SEARCH_LIMIT | 4 | Recuerdos por búsqueda |
| SIGNIFICANT_MEMORY_PROMPT_LIMIT | 4 | Recuerdos significativos |
| BOND_EVENT_PROMPT_LIMIT | 4 | Eventos de vínculo |
| INITIATIVE_ACTION_PROMPT_LIMIT | 3 | Acciones en prompt |
| ASYNC_MEMORY_PERSISTENCE | true | Persistencia asíncrona |
| INITIATIVE_AUTONOMY_ENABLED | true | Loop proactivo |
| INITIATIVE_TICK_SECONDS | 30 | Frecuencia loop |
| INITIATIVE_IDLE_THRESHOLD_SECONDS | 1800 | Inactividad mínima |
| INITIATIVE_COOLDOWN_SECONDS | 1800 | Cooldown |
| INITIATIVE_MAX_PENDING_ACTIONS | 5 | Máximo pendientes |
| GOAL_STATE_PATH | storage/goals.json | Archivo objetivos |
| GOAL_PROMPT_LIMIT | 8 | Objetivos en prompt |
| VOSK_MODEL_PATH | /app/models/vosk/vosk-model-small-es-0.42 | Modelo STT |
| STT_SAMPLE_RATE | 16000 | Frecuencia STT |
| PIPER_MODEL_PATH | /app/models/piper/es_MX-claude-high.onnx | Modelo TTS |
| PIPER_CONFIG_PATH | /app/models/piper/es_MX-claude-high.onnx.json | Config Piper |
| TTS_OUTPUT_DIR | /app/storage/tts | Audio generado |
| TTS_DEFAULT_EMOTION | neutral | Estilo inicial |

## URLs fuera de Docker

Si el backend corre en el host, usa:

~~~env
OLLAMA_BASE_URL=http://127.0.0.1:11434
QDRANT_URL=http://127.0.0.1:6333
~~~

QDRANT_VECTOR_SIZE debe coincidir con el tamaño real de embeddings. No cambies la dimensión sin migrar/recrear la colección y validar compatibilidad.

## Agente de escritorio

- ALETHEIA_DESKTOP_HOST: default 127.0.0.1.
- ALETHEIA_DESKTOP_PORT: default 8765.
- ALETHEIA_DESKTOP_ALLOWED_APPS: objeto JSON alias -> arrays de argumentos.
- ALETHEIA_DESKTOP_CORS_ORIGINS: orígenes permitidos.
- ALETHEIA_DESKTOP_MAX_CAPTURE_WIDTH: ancho máximo captura.
- ALETHEIA_DESKTOP_TOKEN_FILE: ruta del token compartido.

Ejemplo Linux:
~~~bash
export ALETHEIA_DESKTOP_ALLOWED_APPS='{"editor":["code"],"files":["thunar"]}'
~~~

No uses comandos de shell compuestos. Cada array se ejecuta directamente con shell deshabilitado.
