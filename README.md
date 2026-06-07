# Aletheia Local MVP

Agente IA local con FastAPI, Ollama y Qdrant.

## Objetivo del MVP

- Ejecutar un LLM local mediante Ollama en Docker.
- Exponer una API local con FastAPI.
- Guardar memoria semántica en Qdrant.
- Mantener arquitectura modular por capas.
- Preparar el proyecto para agregar STT, TTS, "visión" y "motor emocional".

## Requisitos

- Docker Desktop o Docker Engine.
- Docker Compose.
- Python 3.12 si se ejecuta fuera de Docker.
- GPU NVIDIA opcional para acelerar Ollama.

## Inicio rápido

```bash
cp .env.example .env
docker compose up -d --build
```

Luego descarga un modelo dentro del contenedor de Ollama:

```bash
docker exec -it aletheia_ollama ollama pull llama3.2:3b
```

Prueba la API:

```bash
curl http://localhost:8000/health
```

Envía un mensaje:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hola Aletheia, preséntate brevemente"}'
```

## Estructura

```txt
app/
  api/              # Rutas FastAPI
  application/      # Casos de uso
  core/             # Config, eventos, logs
  domain/           # Entidades, contratos, reglas puras
  infrastructure/   # Ollama, Qdrant, persistencia externa
  modules/          # STT, TTS, visión, emociones
scripts/            # Scripts auxiliares
models/             # Modelos locales montados
storage/            # Datos persistentes locales
```

## Comandos útiles

```bash
make up
make down
make logs
make pull-model MODEL=llama3.2:3b
make chat MSG="Hola"
```

## Nota de arquitectura

Este repositorio arranca con una API modular y servicios externos locales en Docker. Para el MVP práctico, Ollama y Qdrant viven como contenedores separados porque son servicios pesados y especializados. El código Python mantiene separación por capas para evitar un monstruo de espagueti con GPU.
