# Aletheia: evolución de compañera virtual

## Qué cambia en esta entrega

Esta entrega convierte la iniciativa conversacional en un ciclo de aplicación real y añade continuidad mediante objetivos persistentes. No pretende demostrar conciencia ni sentimientos subjetivos. Implementa comportamiento observable y comprobable: estado persistente, seguimiento contextual, iniciativa en segundo plano y controles para el usuario.

### 1. Iniciativa autónoma

- El backend ejecuta `InitiativeAutonomyLoop` durante el ciclo de vida de FastAPI.
- El loop revisa la inactividad cada `INITIATIVE_TICK_SECONDS`.
- Solo puede proponer una iniciativa si ya existe una observación de conversación, se supera el umbral de inactividad y se respeta el cooldown.
- Las acciones espontáneas se distinguen de las sugerencias heurísticas generadas al procesar un mensaje.
- Cada iniciativa tiene estado de entrega y descarte. La interfaz no debe volver a mostrar una iniciativa ya confirmada.
- El usuario puede pausar o reanudar la iniciativa desde la interfaz.

### 2. Objetivos persistentes

- `GoalEngine` registra objetivos expresados directamente con patrones conservadores.
- `GoalStore` persiste los objetivos en `storage/goals.json` con escritura atómica.
- `ChatUseCase` incluye los objetivos relevantes en el contexto del modelo.
- El loop puede retomar un objetivo activo con una pregunta de baja presión.
- La interfaz permite añadir y completar objetivos.
- El texto del usuario nunca se interpreta como un objetivo propio de Aletheia: es contexto que ella puede retomar si resulta pertinente.

### 3. Personalidad y lenguaje

- El perfil de personalidad persistente se conserva, pero el prompt ahora traduce sus rasgos en pautas conductuales concretas: curiosidad, independencia, calidez, humor contextual, espontaneidad moderada y respeto por el silencio.
- La política distingue rasgos de estilo de afirmaciones sobre sentimientos reales.
- La normalización de texto compartida reduce fallos causados por tildes en heurísticas españolas como “te gustaría” y “qué opinas”.
- Las sugerencias no obligan al modelo a formular una pregunta en cada respuesta ni a fingir que realizó trabajo en segundo plano.

### 4. API y resiliencia

Nuevos endpoints:

- `GET /api/initiative/pending`
- `POST /api/initiative/{action_id}/delivered`
- `POST /api/initiative/{action_id}/dismiss`
- `POST /api/initiative/autonomy`
- `GET /api/goals`
- `POST /api/goals`
- `POST /api/goals/{goal_id}/complete`

Las importaciones de Qdrant y de los motores de voz se difieren hasta que se usan esos servicios. Esto permite que el endpoint de salud y las pruebas básicas no requieran inicializar servicios externos ni cargar modelos locales.

## Archivos principales modificados

- `app/application/initiative_autonomy_loop.py`: ciclo de fondo y seguimiento de objetivos.
- `app/application/chat_use_case.py`: observación de objetivos y contexto cognitivo.
- `app/application/prompt_builder.py`: pautas para continuidad, estilo y honestidad.
- `app/api/routes.py`, `app/api/schemas.py`: API de iniciativa y objetivos.
- `app/core/config.py`, `.env.example`: configuración del loop y los objetivos.
- `app/domain/cognitive_workspace.py`: sección de objetivos en el contexto.
- `app/infrastructure/initiative_store.py`: persistencia atómica y migración compatible de acciones antiguas.
- `app/infrastructure/goal_store.py`: persistencia de objetivos.
- `app/modules/initiative_engine.py`: cooldown, entrega, descarte y pausa.
- `app/modules/goal_engine.py`: detección explícita, deduplicación y seguimiento.
- `app/modules/emotion_engine.py`, `app/core/text_normalization.py`: normalización para heurísticas.
- `app/modules/personality_engine.py`: traducción de rasgos en pautas de conversación.
- `ui/src/App.tsx`, `ui/src/api/aletheiaApi.ts`, `ui/src/types.ts`, `ui/src/styles.css`: presentación y control de iniciativas y objetivos.
- `tests/`: pruebas de motores, persistencia, contexto, endpoints y estado de salud.

## Principios SOLID aplicados

- **Responsabilidad única:** `GoalEngine` decide y mantiene objetivos; `GoalStore` persiste; `InitiativeAutonomyLoop` programa evaluaciones; `InitiativeEngine` decide y mantiene el estado de iniciativa; los endpoints traducen solicitudes HTTP.
- **Abierto/cerrado:** las nuevas capacidades se añaden como módulos y contratos separados en lugar de convertir `ChatUseCase` en un motor universal.
- **Inversión de dependencias:** el caso de uso recibe motores y stores mediante su constructor.
- **Separación de infraestructura y dominio:** el motor de objetivos no depende de FastAPI, Qdrant ni Ollama.
- **Resiliencia:** las escrituras de estado se reemplazan atómicamente para evitar JSON parcialmente escrito.

## Configuración de prueba

Para probar la iniciativa sin esperar media hora, usa temporalmente en `.env`:

```env
INITIATIVE_AUTONOMY_ENABLED=true
INITIATIVE_TICK_SECONDS=5
INITIATIVE_IDLE_THRESHOLD_SECONDS=60
INITIATIVE_COOLDOWN_SECONDS=120
```

Reinicia el backend, envía un mensaje y espera un minuto. La iniciativa solo aparece si existe una observación de chat previa. Cuando termines la prueba, restaura los tiempos de producción que prefieras.

## Validación realizada en esta entrega

- `python -m compileall -q app tests`: correcto.
- `pytest -q`: **16 pruebas superadas**.
- La suite incluye pruebas de salud de API, creación y finalización de objetivos, persistencia, pausa de iniciativa, cooldown, entrega idempotente e inclusión de objetivos en el prompt.
- No fue posible instalar las dependencias de Node desde este entorno por falta de conectividad de red. Por tanto, el build de la interfaz no se declara verificado. En un entorno con red, ejecutar `cd ui && npm ci && npm run lint && npm run build`.

## Instalación segura

1. Haz copia de seguridad de tu `.env` y de la carpeta `storage/`.
2. Descomprime el paquete en una carpeta temporal.
3. Copia el código actualizado sobre tu proyecto. Conserva tu `.env`, los JSON existentes de `storage/`, los modelos locales y cualquier audio o recuerdo.
4. En tu proyecto, compara `.env.example` y añade las nuevas variables si quieres configurarlas.
5. Ejecuta `pytest -q`.
6. Reconstruye y levanta los servicios con `docker compose up -d --build`.
7. Abre la interfaz y prueba el botón de iniciativa y el panel de objetivos.

El paquete omite deliberadamente `.env`, `.git`, los estados JSON personales de `storage/`, los modelos y `node_modules`. Así no reemplaza secretos, recuerdos o modelos locales al actualizar el código.
