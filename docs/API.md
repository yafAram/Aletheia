# API HTTP

Base local: http://127.0.0.1:8000. FastAPI publica OpenAPI en /openapi.json y Swagger en /docs.

## Chat y memoria
- GET /health
- POST /api/chat — JSON: message y use_memory.
- GET /api/memory?limit=20
- DELETE /api/memory — acción destructiva.

Ejemplo:
~~~bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hola Aletheia","use_memory":true}'
~~~

## Estado
- GET /api/emotion
- GET /api/personality
- POST /api/personality/reset
- GET /api/self
- POST /api/self/reset
- GET /api/relationships
- GET /api/significant-memories
- GET /api/bond
- GET /api/bond/events
- POST /api/bond/reset

## Percepción e iniciativa
- POST /api/perception
- GET /api/initiative
- GET /api/initiative/actions
- POST /api/initiative/use
- POST /api/initiative/reset
- GET /api/initiative/pending
- POST /api/initiative/autonomy
- POST /api/initiative/{action_id}/delivered
- POST /api/initiative/{action_id}/dismiss

Ejemplo para pausar:
~~~bash
curl -X POST http://127.0.0.1:8000/api/initiative/autonomy \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
~~~

## Objetivos
- GET /api/goals
- POST /api/goals
- POST /api/goals/{goal_id}/complete

Ejemplo:
~~~bash
curl -X POST http://127.0.0.1:8000/api/goals \
  -H "Content-Type: application/json" \
  -d '{"description":"Evaluar recuperación de memoria","priority":0.8}'
~~~

## Voz
- POST /api/stt/transcribe
- POST /api/voice/chat
- POST /api/tts/speak
- GET /api/tts/audio/{filename}
- POST /api/voice/chat/tts

Consulta Swagger para esquemas multipart/form-data y JSON exactos.

## Agente local
En http://127.0.0.1:8765:
- GET /health (sin token)
- GET /v1/apps (Bearer)
- POST /v1/apps/open (Bearer)
- POST /v1/browser/open (Bearer)
- POST /v1/screen/capture (Bearer)

El puente IPC de Electron integra actualmente health, listado y apertura de apps; navegador/captura no están conectados a la UI.
