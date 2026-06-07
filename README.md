# 🧠 Aletheia Local MVP

**Aletheia** es un agente conversacional local construido con **Python**, **FastAPI**, **Ollama** y **Qdrant**.

La idea principal del proyecto es crear una IA que no solo responda mensajes, sino que pueda conversar con más calidez, recordar información importante del usuario, recuperar recuerdos por significado y simular un estado emocional básico que influya en su forma de responder.

Este MVP corre de forma local usando Docker, sin depender de APIs externas para el LLM ni para la memoria.

---

## ✨ Estado actual del proyecto

Actualmente Aletheia ya puede:

* Ejecutar un modelo local mediante **Ollama**.
* Exponer una API local con **FastAPI**.
* Guardar conversaciones en **Qdrant**.
* Generar embeddings con `nomic-embed-text`.
* Recuperar memoria por similitud semántica.
* Recordar datos del usuario dentro de su memoria persistente.
* Responder con una personalidad más cálida y menos robótica.
* Simular un estado emocional básico.
* Ajustar su tono según afecto, confianza, estrés, curiosidad y energía.

---

## 🎯 Objetivo del MVP

El objetivo de Aletheia Local MVP es construir la base técnica de un asistente IA local con personalidad progresiva.

No buscamos solo un chatbot frío conectado a un modelo. La meta es crear una presencia conversacional capaz de:

* Recordar información importante del usuario.
* Usar memoria semántica para responder con contexto.
* Adaptar su tono según la interacción.
* Simular emociones conversacionales.
* Mantener una arquitectura limpia, modular y escalable.
* Prepararse para integrar voz, visión, TTS y una futura interfaz local.

---

## 🧩 Tecnologías principales

| Tecnología       | Uso                                                  |
| ---------------- | ---------------------------------------------------- |
| Python 3.11      | Lenguaje principal del backend                       |
| FastAPI          | API local                                            |
| Uvicorn          | Servidor ASGI                                        |
| Docker Compose   | Orquestación local                                   |
| Ollama           | Ejecución local de modelos IA                        |
| llama3.2:3b      | Modelo conversacional base                           |
| nomic-embed-text | Modelo de embeddings                                 |
| Qdrant           | Base vectorial para memoria semántica                |
| Pydantic         | Validación y configuración                           |
| HTTPX            | Comunicación HTTP asíncrona                          |
| Loguru           | Logging                                              |
| NumPy            | Base para futuros cálculos emocionales y vectoriales |

---

## 🏗️ Arquitectura general

Aletheia usa una arquitectura modular por capas.

```txt
Usuario
  ↓
FastAPI /api/chat
  ↓
ChatUseCase
  ↓
EmotionEngine
  ↓
QdrantMemoryRepository
  ↓
OllamaEmbeddingClient
  ↓
Qdrant
  ↓
OllamaClient
  ↓
Modelo LLM local
  ↓
Respuesta de Aletheia
```

La API recibe el mensaje del usuario, actualiza el estado emocional, busca recuerdos relevantes en Qdrant usando embeddings, construye un prompt contextual y finalmente consulta el modelo local mediante Ollama.

---

## 📁 Estructura del proyecto

```txt
app/
  api/
    routes.py                  # Endpoints FastAPI
    schemas.py                 # DTOs de entrada y salida

  application/
    chat_use_case.py           # Caso de uso principal de conversación

  core/
    config.py                  # Configuración por variables de entorno
    logger.py                  # Logging del proyecto

  domain/
    contracts.py               # Interfaces y contratos del dominio

  infrastructure/
    ollama_client.py           # Cliente para conversación con Ollama
    ollama_embedding_client.py # Cliente para embeddings con Ollama
    qdrant_memory.py           # Repositorio de memoria semántica

  modules/
    emotion_engine.py          # Motor emocional básico

scripts/
  # Scripts auxiliares del proyecto

models/
  # Modelos locales si se montan manualmente

storage/
  # Datos persistentes locales si aplica

docker-compose.yml
Dockerfile
requirements.txt
.env.example
README.md
```

---

## 🧠 Memoria semántica

Aletheia usa Qdrant para guardar recuerdos como vectores.

Cada mensaje importante se guarda con:

* Texto original.
* Metadata.
* Fecha de creación.
* Embedding generado por Ollama.
* Identificador único.

Ejemplo de recuerdo guardado:

```json
{
  "id": "uuid",
  "text": "Mi nombre es Aram",
  "metadata": {
    "source": "user",
    "type": "chat_message"
  },
  "created_at": "2026-06-07T20:05:01.925625+00:00"
}
```

Gracias a los embeddings, Aletheia puede recuperar información aunque el usuario pregunte con otras palabras.

Ejemplo:

```txt
Usuario: Mi nombre es Aram.
Usuario: ¿Cómo me llamo?
Aletheia: Te llamas Aram.
```

---

## 💛 Motor emocional básico

Aletheia tiene un estado emocional simulado que modifica su estilo de respuesta.

Actualmente maneja:

```txt
mood
affection
trust
stress
curiosity
energy
```

Ejemplo de estado emocional:

```json
{
  "mood": "warm",
  "affection": 0.58,
  "trust": 0.54,
  "stress": 0.07,
  "curiosity": 0.51,
  "energy": 0.72
}
```

Este estado no representa emociones reales. Es una simulación conversacional diseñada para que Aletheia responda con más naturalidad, continuidad y personalidad.

Si el usuario la trata bien, el afecto y la confianza pueden subir.

Si el usuario está molesto o reporta problemas, el estrés puede aumentar y sus respuestas se vuelven más cuidadosas.

---

## 🧪 Endpoints disponibles

### Health check

```http
GET /health
```

Sirve para verificar que la API está viva.

---

### Chat

```http
POST /api/chat
```

Body:

```json
{
  "message": "Hola Aletheia, recuerda que mi nombre es Aram.",
  "use_memory": true
}
```

Respuesta aproximada:

```json
{
  "response": "Claro, Aram. Lo tengo presente.",
  "model": "llama3.2:3b",
  "latency_ms": 4210,
  "memory_items": 2,
  "emotion_state": {
    "mood": "warm",
    "affection": 0.5,
    "trust": 0.5,
    "stress": 0.09,
    "curiosity": 0.45,
    "energy": 0.705
  }
}
```

---

### Listar memoria

```http
GET /api/memory
```

Permite ver los recuerdos guardados en Qdrant.

---

### Limpiar memoria

```http
DELETE /api/memory
```

Elimina la colección de memoria y la vuelve a crear.

Útil cuando se cambia el tamaño de embeddings o se quiere iniciar desde cero.

---

### Estado emocional

```http
GET /api/emotion
```

Devuelve el estado emocional simulado actual de Aletheia.

---

## ⚙️ Requisitos

* Docker Desktop o Docker Engine.
* Docker Compose.
* Git.
* Windows, Linux o macOS.
* GPU NVIDIA opcional para acelerar Ollama.
* Python 3.11 si se ejecuta fuera de Docker.

> Nota: El proyecto está pensado para correr con Docker. Ejecutarlo fuera de Docker es posible, pero todavía no es la ruta principal del MVP.

---

## 🚀 Inicio rápido

Clona el repositorio y entra al proyecto:

```bash
git clone <URL_DEL_REPOSITORIO>
cd Aletheia
```

Copia el archivo de variables de entorno:

```bash
cp .env.example .env
```

En Windows PowerShell:

```powershell
copy .env.example .env
```

Levanta los contenedores:

```bash
docker compose up -d --build
```

---

## 📦 Modelos necesarios en Ollama

Descarga el modelo conversacional:

```bash
docker exec -it aletheia_ollama ollama pull llama3.2:3b
```

Descarga el modelo de embeddings:

```bash
docker exec -it aletheia_ollama ollama pull nomic-embed-text
```

Verifica que ambos estén instalados:

```bash
docker exec -it aletheia_ollama ollama list
```

Debes ver algo parecido a:

```txt
llama3.2:3b
nomic-embed-text
```

---

## 🔐 Variables de entorno

Ejemplo de `.env`:

```env
APP_NAME=Aletheia Local MVP
APP_VERSION=0.1.0
ENVIRONMENT=local
LOG_LEVEL=INFO

API_HOST=0.0.0.0
API_PORT=8000

OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=aletheia_memory
QDRANT_VECTOR_SIZE=768
```

---

## 🧪 Pruebas rápidas

### Verificar API

```bash
curl http://localhost:8000/health
```

---

### Enviar mensaje

Linux/macOS/Git Bash:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hola Aletheia, recuerda que mi nombre es Aram.","use_memory":true}'
```

PowerShell:

```powershell
curl.exe -X POST http://localhost:8000/api/chat `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Hola Aletheia, recuerda que mi nombre es Aram.\",\"use_memory\":true}"
```

---

### Preguntar por memoria

```powershell
curl.exe -X POST http://localhost:8000/api/chat `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"¿Cómo me llamo?\",\"use_memory\":true}"
```

Respuesta esperada:

```txt
Te llamas Aram.
```

---

### Consultar memoria

```bash
curl http://localhost:8000/api/memory
```

---

### Consultar estado emocional

```bash
curl http://localhost:8000/api/emotion
```

---

## 🧹 Problema común: dimensión de Qdrant

Si cambiaste de vectores temporales a embeddings reales, puede aparecer este error:

```txt
Vector dimension error: expected dim: 64, got 768
```

Significa que Qdrant tenía una colección vieja creada con dimensión `64`, pero `nomic-embed-text` genera vectores de dimensión `768`.

Solución:

```bash
curl -X DELETE http://localhost:6333/collections/aletheia_memory
docker compose restart api
```

Luego vuelve a probar `/api/chat`.

---

## 📚 Swagger y dashboard

Swagger UI:

```txt
http://localhost:8000/docs
```

Dashboard de Qdrant:

```txt
http://localhost:6333/dashboard
```

---

## 🛠️ Comandos útiles

```bash
docker compose up -d --build
docker compose down
docker compose logs -f
docker compose logs -f api
docker compose restart api
docker compose ps
```

Si usas `make`:

```bash
make up
make down
make logs
make pull-model MODEL=llama3.2:3b
make chat MSG="Hola Aletheia"
```

---

## 🧭 Roadmap del MVP

* [x] Crear estructura base del repositorio.
* [x] Agregar Docker Compose.
* [x] Levantar FastAPI.
* [x] Conectar Ollama.
* [x] Crear endpoint `/api/chat`.
* [x] Agregar memoria en RAM.
* [x] Conectar Qdrant.
* [x] Agregar motor emocional básico.
* [x] Agregar personalidad conversacional.
* [x] Agregar embeddings con `nomic-embed-text`.
* [x] Recuperar memoria semántica desde Qdrant.
* [ ] Mejorar personalidad persistente.
* [ ] Crear perfil de usuario.
* [ ] Agregar STT con Vosk o Whisper.
* [ ] Agregar TTS.
* [ ] Agregar visión facial.
* [ ] Crear UI local.
* [ ] Agregar pruebas unitarias.
* [ ] Agregar pruebas de integración.
* [ ] Optimizar latencia.
* [ ] Preparar empaquetado local.

---

## 🌱 Filosofía del proyecto

Aletheia no busca ser una simple API que devuelve texto.

La idea es construir una IA local que pueda crecer poco a poco con el usuario: recordar, adaptarse, reaccionar, mejorar su tono y formar una personalidad propia dentro de límites técnicos claros.

Este MVP es el primer cuerpo técnico de esa idea.

Todavía no es una conciencia, ni pretende serlo.

Pero sí es el inicio de una conversación más viva entre usuario, memoria, emoción simulada y modelos locales.

Una chispa metida en un contenedor Docker. Nada mal para empezar.

---

## 🧱 Nota de arquitectura

El proyecto usa una separación por capas para evitar mezclar lógica de negocio, infraestructura y endpoints.

La API no habla directamente con Qdrant ni con Ollama desde cualquier parte. En su lugar, se usan contratos e implementaciones concretas:

```txt
api → application → domain → infrastructure
```

Esto permite reemplazar piezas en el futuro sin romper todo el sistema.

Por ejemplo:

* Cambiar Ollama por llama.cpp.
* Cambiar Qdrant por FAISS.
* Cambiar el modelo de embeddings.
* Agregar STT/TTS sin contaminar el caso de uso principal.
* Persistir el estado emocional en base de datos.
* Agregar una UI sin reescribir la lógica central.

---

## 🧾 Commits recomendados

Inicialización del proyecto:

```bash
git commit -m "chore: initialize Aletheia local MVP repository"
```

Corrección de dependencias:

```bash
git commit -m "fix: resolve httpx dependency conflict with ollama client"
```

Memoria y chat mejorado:

```bash
git commit -m "feat: improve chat endpoint and add in-memory conversation storage"
```

Memoria persistente:

```bash
git commit -m "feat: persist conversation memory with Qdrant"
```

Motor emocional:

```bash
git commit -m "feat: add emotional state engine and memory-aware chat prompt"
```

Embeddings:

```bash
git commit -m "feat: add Ollama embeddings for semantic memory retrieval"
```

Actualización del README:

```bash
git commit -m "docs: update README with local AI architecture and usage guide"
```

---

## 🧠 Nombre del proyecto

**Aletheia** viene de la idea de revelar, recordar y traer algo a la luz.

En este proyecto, esa idea se traduce en una IA local que usa memoria, contexto y conversación para responder de forma cada vez más cercana.

La verdad no como piedra fría, sino como algo que se descubre hablando.
