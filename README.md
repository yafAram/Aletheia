# Aletheia

**Asistente de IA local, modular y extensible**  
Python 3.11 · FastAPI · Ollama · Qdrant · React · TypeScript · Electron

Aletheia es un proyecto personal de ingeniería de software que explora cómo construir un asistente conversacional que conserve contexto entre sesiones, organice objetivos explícitos, adapte su estilo de respuesta y proponga iniciativas limitadas mediante reglas configurables. La inferencia se ejecuta mediante Ollama, la recuperación semántica utiliza Qdrant y la experiencia de usuario se ofrece mediante una interfaz web y una compañera de escritorio llamada **Lumina**.

> **Estado:** MVP experimental en desarrollo. El repositorio contiene backend, persistencia, motores de dominio, API, UI y agente de escritorio. No se presenta como producto comercial terminado ni como IA consciente. Las pruebas automatizadas no equivalen a validar todos los flujos en hardware real.

## Contenido

- [Visión](#visión)
- [Funcionalidades](#funcionalidades)
- [Límites actuales](#límites-actuales)
- [Arquitectura](#arquitectura)
- [Tecnologías y versiones](#tecnologías-y-versiones)
- [Estructura](#estructura)
- [Requisitos](#requisitos)
- [Instalación rápida](#instalación-rápida)
- [Instalación por componente](#instalación-por-componente)
- [Configuración](#configuración)
- [Voz](#voz-stt-y-tts)
- [Agente de escritorio](#agente-de-escritorio)
- [API](#api-http)
- [Pruebas](#pruebas-y-calidad)
- [Datos y actualización](#persistencia-respaldos-y-actualización)
- [Seguridad](#seguridad-y-privacidad)
- [Fundamentos](#fundamentos-y-decisiones-de-diseño)
- [Roadmap](#versionado-y-roadmap)
- [Documentación](#documentación)
- [Autor](#autor)

## Visión

El proyecto aborda cinco retos:

1. **Continuidad conversacional:** recuperar recuerdos semánticamente relevantes sin reenviar todo el historial en cada turno.
2. **Contexto explícito:** separar personalidad, objetivos, emoción simulada, relaciones e iniciativas.
3. **Autonomía acotada:** proponer acciones solo cuando se cumplen condiciones observables y el usuario conserva controles.
4. **Ejecución local:** usar modelos y servicios que pueden ejecutarse en el propio equipo.
5. **Integración de escritorio:** separar las acciones del sistema operativo de la API conversacional y protegerlas mediante autenticación y permisos explícitos.

## Funcionalidades

### Conversación con modelo local

- API FastAPI y cliente Ollama.
- Modelo de chat predeterminado: llama3.2:3b.
- Parámetros configurables: temperatura, top-p, tokens de salida, ventana de contexto y keep-alive.
- Respuesta con latencia y metadatos del contexto.
- La interfaz web y Lumina utilizan la misma API.

### Memoria semántica con Qdrant

- Ollama genera embeddings a partir del texto.
- Qdrant almacena vectores y payload con texto, metadatos e instante de creación.
- La búsqueda recupera recuerdos relevantes para el turno actual.
- Colección predeterminada: aletheia_memory.
- Modelo de embeddings predeterminado: nomic-embed-text.
- Dimensión configurada: 768; el modelo elegido debe producir vectores compatibles.
- El límite de búsqueda y la cantidad de recuerdos incluidos en el prompt son configurables.

Qdrant no es por sí solo una memoria autobiográfica humana. El proyecto combina recuperación vectorial con estados estructurados guardados en archivos locales.

### Estado, personalidad y relaciones

Los motores independientes mantienen:
- **Emoción simulada:** ánimo, energía, estrés, curiosidad, confianza y afecto como variables computacionales heurísticas.
- **Personalidad:** rasgos numéricos que se convierten en pautas de estilo mediante el constructor del prompt.
- **Estado propio:** estructura de estado y recuerdos significativos.
- **Relaciones/vínculo:** estados y eventos persistentes que pueden influir en el contexto.
- **Normalización de texto:** tratamiento de mayúsculas, tildes y espacios para robustecer heurísticas en español.

Estos módulos aportan señales al prompt; no sustituyen al modelo de lenguaje ni representan sentimientos subjetivos.

### Objetivos persistentes

- Detección conservadora de expresiones explícitas como “quiero desarrollar…” o “mi objetivo es…”.
- Evita convertir cualquier pregunta o comentario ambiguo en un objetivo.
- Deduplicación, prioridad, confianza, estado y fechas.
- Creación manual y finalización desde la API/UI.
- Recuperación de objetivos activos para continuidad conversacional.
- Persistencia local en storage/goals.json.

### Iniciativa conversacional

InitiativeAutonomyLoop se ejecuta durante el ciclo de vida de FastAPI. Considera:
- Observación previa de conversación.
- Umbral de inactividad.
- Frecuencia de evaluación.
- Cooldown entre propuestas.
- Límite de acciones pendientes.
- Pausa/reanudación controlada por el usuario.
- Estados de entrega y descarte.

No representa trabajo secreto ni ejecución ilimitada en segundo plano. Es un loop de evaluación con reglas explícitas.

### Voz

- STT con Vosk.
- TTS con Piper.
- Conversación por voz y síntesis mediante endpoints específicos.
- La voz es opcional; el chat de texto no requiere modelos de voz.

Los modelos no están incluidos en Git y deben instalarse por separado.

### Web y Lumina Desktop

La carpeta ui contiene React, TypeScript y Vite. El punto de entrada carga:
- Interfaz web normal sin parámetro.
- Lumina cuando se usa el parámetro ?desktop=1.

Electron implementa ventana flotante, bandeja, atajo Ctrl+Shift+L y configuración de inicio automático. El renderer usa preload/IPC y no recibe acceso Node directo.

### Agente local

desktop_agent se ejecuta en el sistema anfitrión, no dentro del contenedor de la API:
- Salud del proceso.
- Listado de aplicaciones autorizadas.
- Apertura de alias permitidos.
- Apertura de URL HTTP/HTTPS mediante navegador predeterminado.
- Captura manual de pantalla de una sola toma, si están instalados mss y Pillow.

El agente valida Bearer token, usa allowlist y lanza procesos con shell=False. La UI Electron actual integra health, listado y apertura de aplicaciones; no todas las rutas del agente están conectadas a la interfaz.

## Límites actuales

- No tiene conciencia, voluntad, emociones humanas ni experiencia subjetiva.
- No existe autonomía general para ejecutar cualquier tarea del equipo.
- No interpreta continuamente pantalla ni graba audio/video en segundo plano.
- No hay automatización general de teclado y ratón.
- La captura de pantalla es manual, no una función de visión continua.
- No todas las rutas del agente están integradas en Lumina.
- La calidad de memoria depende de embeddings, consulta, límites y datos disponibles.
- STT/TTS requieren modelos compatibles instalados localmente.
- No se garantiza compatibilidad con cualquier GPU, sistema operativo o dispositivo de audio.
- La API principal no implementa autenticación de usuarios; no debe exponerse públicamente.

## Arquitectura

~~~mermaid
flowchart TB
    WEB[React Web UI] --> API[FastAPI API]
    LUMINA[Electron / React - Lumina] --> API
    LUMINA --> AGENT[Desktop Agent - FastAPI]
    API --> CHAT[ChatUseCase]
    CHAT --> PROMPT[PromptBuilder / CognitiveWorkspace]
    CHAT --> ENGINES[Domain Engines]
    ENGINES --> GOALS[Goals]
    ENGINES --> INIT[Initiative]
    ENGINES --> PERSONALITY[Personality / Emotion]
    ENGINES --> REL[Relationships / Self state]
    CHAT --> OLLAMA[Ollama local LLM]
    CHAT --> MEMORY[Memory Repository]
    MEMORY --> EMB[Ollama Embeddings]
    MEMORY --> QDRANT[(Qdrant)]
    ENGINES --> JSON[(Local JSON stores)]
    API --> VOICE[Vosk STT / Piper TTS]
    AGENT --> OS[Host OS - allowlisted actions]
~~~

### Flujo de chat

1. La UI envía POST /api/chat con mensaje y use_memory.
2. FastAPI valida la solicitud.
3. ChatUseCase recupera recuerdos semánticos cuando corresponde.
4. Los motores aportan objetivos y estado estructurado.
5. PromptBuilder organiza el contexto y las reglas.
6. Ollama genera la respuesta.
7. La API devuelve respuesta, latencia y metadatos.
8. La persistencia de memoria sigue la configuración correspondiente.

### Responsabilidades

| Capa | Responsabilidad |
|---|---|
| app/api | Rutas, dependencias y esquemas HTTP |
| app/application | Casos de uso y loop de iniciativa |
| app/domain | Contratos, entidades y contexto cognitivo |
| app/modules | Motores de personalidad, objetivos, emoción, iniciativa, relaciones, STT y TTS |
| app/infrastructure | Adaptadores Ollama/Qdrant y stores locales |
| desktop_agent | API local de acciones acotadas |
| ui | React, Electron, preload y puente IPC |
| tests | Pruebas automatizadas |

## Tecnologías y versiones

Versiones obtenidas de los manifiestos del repositorio; no implican certificación de todas las combinaciones de hardware/SO.

| Componente | Versión/configuración |
|---|---|
| Python | 3.11 |
| FastAPI | 0.115.6 |
| Uvicorn | 0.34.0 |
| Pydantic | 2.10.4 |
| Pydantic Settings | 2.7.1 |
| Qdrant Python client | 1.12.1 |
| Qdrant Server | 1.12.1 |
| Ollama Python client | 0.4.5 |
| Modelo LLM | llama3.2:3b |
| Embeddings | nomic-embed-text |
| Vosk | 0.3.45 |
| Piper TTS | 1.4.2 |
| React / React DOM | 19.2.6 |
| Vite | 8.0.12 |
| TypeScript | 6.0.2 |
| Electron | 38.x |
| Electron Builder | 26.x |
| pytest | 8.3.4 |
| pytest-asyncio | 0.25.0 |

Las dependencias exactas están en requirements*.txt y ui/package-lock.json. ui/package.json aún declara 0.0.0; no hay que interpretarlo como release publicada.

## Estructura

~~~text
Aletheia/
├── app/
│   ├── api/                 # Endpoints y esquemas
│   ├── application/         # Chat, prompt e iniciativa
│   ├── core/                # Configuración, eventos y utilidades
│   ├── domain/              # Contratos, entidades y contexto
│   ├── infrastructure/      # Ollama, Qdrant y stores JSON
│   └── modules/             # Motores y módulos de voz
├── desktop_agent/           # Agente local del host
├── docs/                    # Documentación técnica
├── finanzas/nexo_fiance/    # Submódulo independiente y opcional
├── models/                  # Modelos locales ignorados por Git
├── scripts/                 # Utilidades de desarrollo
├── storage/                 # Estado local ignorado por Git
├── tests/                   # Pruebas automatizadas
├── ui/
│   ├── desktop/             # Main/preload Electron
│   └── src/                 # React, API client y Lumina
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── requirements.txt
└── requirements-dev.txt
~~~

El submódulo finanzas/nexo_fiance pertenece a otro repositorio y no es necesario para ejecutar Aletheia. No uses --recurse-submodules si no lo necesitas.

## Requisitos

- Git.
- Docker Engine y Docker Compose plugin.
- Python 3.11.
- Node.js 22 LTS y npm para UI/Electron.
- RAM, CPU/GPU y almacenamiento suficientes para el modelo local.
- Conexión inicial para descargar imágenes, dependencias y modelos. La inferencia puede ejecutarse localmente una vez descargados.

El rendimiento depende del hardware, cuantización y tamaño del modelo.

## Instalación rápida

Todos los comandos iniciales se ejecutan desde la raíz.

### 1. Clonar y configurar

~~~bash
git clone https://github.com/yafAram/Aletheia.git
cd Aletheia
cp .env.example .env
~~~

Windows PowerShell:

~~~powershell
git clone https://github.com/yafAram/Aletheia.git
cd Aletheia
Copy-Item .env.example .env
~~~

Edita .env localmente. Nunca agregues secretos al repositorio.

### 2. Permisos en Linux

~~~bash
export ALETHEIA_UID="$(id -u)"
export ALETHEIA_GID="$(id -g)"
~~~

### 3. Iniciar API, Ollama y Qdrant

~~~bash
docker compose up -d --build
docker compose ps
~~~

Servicios:
- API FastAPI: puerto 8000.
- Ollama: puerto 11434.
- Qdrant: puertos 6333 y 6334.

### 4. Descargar modelos de lenguaje

~~~bash
docker exec -it aletheia_ollama ollama pull llama3.2:3b
docker exec -it aletheia_ollama ollama pull nomic-embed-text
docker exec -it aletheia_ollama ollama list
~~~

### 5. Verificar API

~~~bash
curl http://127.0.0.1:8000/health
~~~

- Swagger: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json

/health solo confirma que FastAPI responde; no comprueba que Ollama, Qdrant o los modelos estén listos.

### 6. Ejecutar UI web

~~~bash
cd ui
npm ci
npm run dev
~~~

Vite muestra la dirección local, normalmente http://localhost:5173.

## Instalación por componente

### Backend nativo en Python

Para ejecutar API sin Docker, instala Ollama y Qdrant en el host y cambia las URLs del .env a 127.0.0.1:

~~~env
OLLAMA_BASE_URL=http://127.0.0.1:11434
QDRANT_URL=http://127.0.0.1:6333
~~~

Después:

~~~bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
~~~

Windows PowerShell para activar el entorno: .\.venv\Scripts\Activate.ps1

### UI web

~~~bash
cd ui
npm ci
npm run dev
~~~

La API debe estar disponible en http://localhost:8000.

### Lumina Desktop

Primero instala el agente en la raíz del repositorio.

Linux/macOS:

~~~bash
python3.11 -m venv .venv-desktop
source .venv-desktop/bin/activate
python -m pip install --upgrade pip
pip install -r desktop_agent/requirements.txt
~~~

Windows PowerShell:

~~~powershell
py -3.11 -m venv .venv-desktop
.\.venv-desktop\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r desktop_agent\requirements.txt
~~~

Después:

~~~bash
cd ui
npm ci
npm run desktop:dev
~~~

La API debe estar activa en localhost:8000. Electron inicia Vite y trata de iniciar el agente local desde .venv-desktop.

### Empaquetar instaladores

Linux AppImage:

~~~bash
cd ui
npm ci
npm run package:linux
~~~

Windows NSIS:

~~~powershell
cd ui
npm ci
npm run package:windows
~~~

Construye y prueba cada instalador en el sistema operativo destino.

## Configuración

Las variables se definen en .env.example y app/core/config.py.

| Variable | Predeterminado | Uso |
|---|---|---|
| APP_NAME | Aletheia Local MVP | Nombre de API |
| APP_VERSION | 0.1.0 | Versión expuesta por health |
| ENVIRONMENT | local | Entorno |
| LOG_LEVEL | INFO | Nivel de log |
| OLLAMA_BASE_URL | http://ollama:11434 | Ollama en Compose |
| OLLAMA_MODEL | llama3.2:3b | Modelo conversacional |
| OLLAMA_EMBEDDING_MODEL | nomic-embed-text | Embeddings |
| QDRANT_URL | http://qdrant:6333 | Qdrant |
| QDRANT_COLLECTION | aletheia_memory | Colección vectorial |
| QDRANT_VECTOR_SIZE | 768 | Dimensión del vector |
| OLLAMA_NUM_PREDICT | 220 | Tokens de salida |
| OLLAMA_TEMPERATURE | 0.7 | Temperatura |
| OLLAMA_TOP_P | 0.9 | Top-p |
| OLLAMA_NUM_CTX | 3072 | Contexto |
| OLLAMA_KEEP_ALIVE | 30m | Permanencia del modelo |
| MEMORY_SEARCH_LIMIT | 4 | Recuerdos por búsqueda |
| SIGNIFICANT_MEMORY_PROMPT_LIMIT | 4 | Recuerdos significativos en prompt |
| BOND_EVENT_PROMPT_LIMIT | 4 | Eventos de vínculo en prompt |
| INITIATIVE_ACTION_PROMPT_LIMIT | 3 | Acciones en prompt |
| ASYNC_MEMORY_PERSISTENCE | true | Persistencia asíncrona |
| INITIATIVE_AUTONOMY_ENABLED | true | Loop proactivo |
| INITIATIVE_TICK_SECONDS | 30 | Frecuencia del loop |
| INITIATIVE_IDLE_THRESHOLD_SECONDS | 1800 | Inactividad mínima |
| INITIATIVE_COOLDOWN_SECONDS | 1800 | Cooldown |
| INITIATIVE_MAX_PENDING_ACTIONS | 5 | Pendientes máximas |
| GOAL_STATE_PATH | storage/goals.json | Archivo de objetivos |
| GOAL_PROMPT_LIMIT | 8 | Objetivos en contexto |
| VOSK_MODEL_PATH | /app/models/vosk/vosk-model-small-es-0.42 | Modelo STT |
| STT_SAMPLE_RATE | 16000 | Frecuencia STT |
| PIPER_MODEL_PATH | /app/models/piper/es_MX-claude-high.onnx | Modelo TTS |
| PIPER_CONFIG_PATH | /app/models/piper/es_MX-claude-high.onnx.json | Configuración Piper |
| TTS_OUTPUT_DIR | /app/storage/tts | Audio generado |
| TTS_DEFAULT_EMOTION | neutral | Estilo TTS inicial |

Los nombres se corresponden con los campos de app/core/config.py. Al agregar una variable, actualiza el ejemplo y esta tabla. La dimensión vectorial debe coincidir con el modelo de embeddings; cambiarla puede requerir migrar/recrear la colección.

## Voz: STT y TTS

Los paquetes Python están fijados, pero los pesos de modelos no se distribuyen en Git.

### STT con Vosk

1. Descarga un modelo Vosk compatible con español.
2. Descomprímelo en models/vosk/.
3. Configura VOSK_MODEL_PATH con la ruta del modelo dentro del contenedor.
4. Verifica que la carpeta exista antes de invocar STT.

El ejemplo usa /app/models/vosk/vosk-model-small-es-0.42.

### TTS con Piper

1. Descarga un modelo Piper compatible y su JSON correspondiente.
2. Coloca el par .onnx y .onnx.json en models/piper/.
3. Configura PIPER_MODEL_PATH y PIPER_CONFIG_PATH.
4. Verifica ambos archivos dentro del contenedor.

El ejemplo referencia es_MX-claude-high.onnx; ese modelo no se incluye en el repositorio. Si eliges otra voz, cambia ambas rutas. No renombres un modelo distinto para simular compatibilidad.

Endpoints de voz:
- POST /api/stt/transcribe
- POST /api/voice/chat
- POST /api/tts/speak
- GET /api/tts/audio/{filename}
- POST /api/voice/chat/tts

## Agente de escritorio

El agente corre en el host porque la API dentro de Docker no controla automáticamente la sesión gráfica.

| Variable | Uso |
|---|---|
| ALETHEIA_DESKTOP_HOST | Host; predeterminado 127.0.0.1 |
| ALETHEIA_DESKTOP_PORT | Puerto; predeterminado 8765 |
| ALETHEIA_DESKTOP_ALLOWED_APPS | Objeto JSON con alias y argumentos |
| ALETHEIA_DESKTOP_CORS_ORIGINS | Orígenes CORS |
| ALETHEIA_DESKTOP_MAX_CAPTURE_WIDTH | Ancho máximo de captura |
| ALETHEIA_DESKTOP_TOKEN_FILE | Archivo del token |

El token se crea normalmente en ~/.config/aletheia/desktop-agent-token. Electron lee ese archivo. No publiques el token ni lo incluyas en capturas.

Ejemplo de allowlist Linux:

~~~bash
export ALETHEIA_DESKTOP_ALLOWED_APPS='{"editor":["code"],"files":["thunar"]}'
~~~

Los valores son arrays de argumentos, no cadenas de shell. El ejecutable debe existir. La captura requiere mss, Pillow y sesión gráfica activa. Es manual, de una sola toma y no guarda la imagen en disco.

Consulta docs/AGENTE_ESCRITORIO.md.

## API HTTP

FastAPI genera OpenAPI; Swagger está en /docs. Resumen de rutas actuales:

| Método | Ruta | Función |
|---|---|---|
| GET | /health | Salud básica |
| POST | /api/chat | Chat con memoria opcional |
| GET / DELETE | /api/memory | Listar o limpiar memoria |
| GET | /api/emotion | Estado emocional simulado |
| GET | /api/personality | Consultar personalidad |
| POST | /api/personality/reset | Restablecer personalidad |
| GET | /api/self | Estado propio y relaciones |
| POST | /api/self/reset | Restablecer estado propio |
| GET | /api/relationships | Consultar relaciones |
| GET | /api/significant-memories | Recuerdos significativos |
| GET | /api/bond | Estado de vínculo |
| GET | /api/bond/events | Eventos del vínculo |
| POST | /api/bond/reset | Restablecer vínculo |
| POST | /api/perception | Registrar observación estructurada |
| GET | /api/initiative | Estado, observaciones y acciones |
| GET | /api/initiative/actions | Historial de iniciativas |
| POST | /api/initiative/use | Marcar acción utilizada |
| POST | /api/initiative/reset | Restablecer iniciativa |
| GET | /api/initiative/pending | Propuestas pendientes |
| POST | /api/initiative/autonomy | Pausar/reanudar autonomía |
| POST | /api/initiative/{action_id}/delivered | Marcar entrega |
| POST | /api/initiative/{action_id}/dismiss | Descartar propuesta |
| GET / POST | /api/goals | Consultar o crear objetivos |
| POST | /api/goals/{goal_id}/complete | Completar objetivo |
| POST | /api/stt/transcribe | Reconocimiento de voz |
| POST | /api/voice/chat | Conversación por voz |
| POST | /api/tts/speak | Síntesis de voz |
| GET | /api/tts/audio/{filename} | Obtener audio |
| POST | /api/voice/chat/tts | Flujo de voz combinado |

Ejemplo de chat:

~~~bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hola Aletheia","use_memory":true}'
~~~

Ejemplo para pausar iniciativa:

~~~bash
curl -X POST http://127.0.0.1:8000/api/initiative/autonomy \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
~~~

Los endpoints de borrado y reset son destructivos para el estado correspondiente. Respalda los datos antes de usarlos.

El agente expone además GET /health, GET /v1/apps, POST /v1/apps/open, POST /v1/browser/open y POST /v1/screen/capture en localhost:8765. Las rutas de acción requieren Bearer token.

## Pruebas y calidad

Instala dependencias de desarrollo:

~~~bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
~~~

Backend:

~~~bash
python -m pytest -q
python -m compileall -q app desktop_agent tests
~~~

UI:

~~~bash
cd ui
npm ci
npm run lint
npm run build
~~~

GitHub Actions valida compilación Python, pytest, instalación UI, ESLint y build TypeScript/Vite.

**Hallazgo CI conocido:** la última ejecución revisada pasó compilación Python y lint/build de UI, pero pytest falló durante la recolección porque Python no resolvía los paquetes locales app y desktop_agent. Se agrega pytest.ini para declarar la raíz del repositorio en pythonpath. El arreglo debe confirmarse con una ejecución posterior verde; no se afirma todavía que el pipeline esté aprobado.

La suite no reemplaza pruebas manuales de Ollama, Qdrant, voz, Electron, captura de pantalla ni sistemas destino.

## Persistencia, respaldos y actualización

Conserva:
- storage/: estados JSON y audio.
- Volumen Docker qdrant_data: memoria vectorial.
- Volumen Docker ollama_data: modelos descargados.
- models/: modelos locales.
- .env: configuración privada.

Antes de actualizar:

~~~bash
docker compose ps
cp -a storage "storage.backup.$(date +%Y%m%d-%H%M%S)"
cp .env .env.backup
~~~

Actualiza código solo después de revisar cambios:

~~~bash
git status
git pull --ff-only
docker compose up -d --build
~~~

No uses docker compose down -v durante mantenimiento normal: elimina volúmenes y puede borrar datos de Qdrant/Ollama.

## Seguridad y privacidad

Local-first no significa automáticamente seguro.

- La API principal no implementa autenticación de usuario. No la expongas a Internet ni redes no confiables.
- Compose publica puertos de API, Ollama y Qdrant. Limita acceso con firewall y red del host; para uso local, enlaza puertos a loopback.
- No expongas Qdrant ni Ollama públicamente.
- Mantén el agente en 127.0.0.1, usa token robusto y allowlist mínima.
- No versiona .env, tokens, claves, conversaciones, datos personales, modelos ni archivos de storage.
- Protege los volúmenes Docker y respaldos.
- Los endpoints destructivos deben protegerse antes de cualquier despliegue multiusuario.
- Consulta SECURITY.md.

## Fundamentos y decisiones de diseño

El diseño se desarrolló mediante iteraciones técnicas, pruebas locales, revisión de logs y decisiones de arquitectura trabajadas durante el proyecto. Los ejes recuperados son:

- **Local-first:** inferencia local y datos bajo control del entorno.
- **Recuperación semántica:** embeddings + búsqueda vectorial para seleccionar contexto relevante.
- **Separación de memoria y estado:** recuerdos en Qdrant y estados estructurados en stores específicos.
- **Motores deterministas alrededor del LLM:** objetivos, iniciativa y personalidad como módulos independientes.
- **Autonomía limitada:** inactividad, cooldown, pendientes, entrega, descarte y pausa.
- **Control humano:** agente de escritorio autenticado y allowlist.

No se recuperó una bibliografía académica concreta de las conversaciones anteriores; por rigor no se inventan papers, autores ni DOI. docs/FUNDAMENTOS_Y_DECISIONES.md explica los patrones y enlaza documentación oficial de las tecnologías. Esas referencias son documentación técnica, no citas de investigaciones académicas.

## Documentación

| Documento | Contenido |
|---|---|
| docs/ARCHITECTURE.md | Arquitectura y responsabilidades |
| docs/FUNDAMENTOS_Y_DECISIONES.md | Fundamentos, trade-offs y referencias técnicas |
| docs/INSTALACION.md | Instalación por sistema y componente |
| docs/CONFIGURACION.md | Variables, modelos y rutas |
| docs/API.md | Endpoints y ejemplos |
| docs/AGENTE_ESCRITORIO.md | Permisos, token e instalación del agente |
| docs/OPERACION.md | Logs, persistencia y diagnóstico |
| docs/PRUEBAS_MVP.md | Pruebas automatizadas y manuales |
| EVOLUCION_ALETHEIA.md | Registro histórico de objetivos e iniciativa |
| CONTRIBUTING.md | Flujo de contribución |
| SECURITY.md | Reporte de vulnerabilidades |

## Versionado y roadmap

Versiones declaradas:
- API: 0.1.0 en APP_VERSION.
- Agente: 0.1.0 en su aplicación FastAPI.
- UI: 0.0.0 en ui/package.json; pendiente alinear releases.

No hay que asumir una release estable publicada. Se propone SemVer (MAJOR.MINOR.PATCH) al comenzar a publicar releases.

### Pendientes priorizados

- [ ] Confirmar CI backend verde y estabilizar configuración pytest.
- [ ] Pruebas de integración aisladas para Qdrant y Ollama.
- [ ] Pruebas API para memoria, relaciones, voz, reset y errores externos.
- [ ] Validar instalación limpia en Windows y Linux.
- [ ] Validar empaquetado Electron por sistema destino.
- [ ] Añadir indicador visual/consentimiento antes de nuevas capacidades de percepción.
- [ ] Añadir autenticación local y protección de origen antes de habilitar acceso remoto.
- [ ] Enlazar puertos Compose a loopback por defecto.
- [ ] Logging estructurado, métricas y diagnóstico de dependencias.
- [ ] Backup/restauración de Qdrant y JSON con pruebas de recuperación.
- [ ] Alinear versiones de API, agente, UI y releases.
- [ ] Decidir si el submódulo financiero debe separarse del ciclo de entrega.

Fuera de alcance hasta implementar controles adecuados: automatización arbitraria, acceso remoto abierto, captura continua y ejecución de shell a partir del texto del modelo.

## Contribuir

Mantén las fronteras de arquitectura, añade pruebas para reglas deterministas y actualiza documentación al cambiar configuración o contratos. Consulta CONTRIBUTING.md. No incluyas secretos, datos personales, modelos o artefactos de build.

## Autor

**Yafte Aram Mercado Meza**  
Software Development Engineering · Backend / AI systems

- GitHub: [@yafAram](https://github.com/yafAram)
- Repositorio: [github.com/yafAram/Aletheia](https://github.com/yafAram/Aletheia)

Aletheia es un proyecto independiente de aprendizaje e ingeniería. La documentación describe el código y sus límites conocidos; el estado de las pruebas debe consultarse en GitHub Actions.
