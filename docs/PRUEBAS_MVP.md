# Matriz de validación MVP

Se distinguen pruebas automatizadas del repositorio y pruebas manuales que requieren servicios, modelos o hardware.

## Automatizadas

| Área | Archivo | Alcance |
|---|---|---|
| API | tests/test_health.py | Salud básica |
| Contexto | tests/test_cognitive_workspace.py | Construcción de contexto |
| Objetivos/iniciativa | tests/test_goal_and_initiative.py | Detección explícita, deduplicación, cooldown, pausa y persistencia |
| API objetivos | tests/test_goal_api.py | Rutas de objetivos |
| Persistencia | tests/test_goal_store_corruption.py | Archivo de objetivos corrupto |
| Personalidad | tests/test_personality_engine.py | Motor de personalidad |
| Agente | tests/test_desktop_agent.py | Configuración y autenticación |
| UI estática | tests/test_patch_static.py | Guardas Electron |
| Texto | tests/test_text_normalization.py | Tildes, mayúsculas y espacios |

La ejecución completa debe verificarse en GitHub Actions. Que una prueba exista no significa que ya haya pasado.

## Pruebas manuales pendientes

| Caso | Resultado esperado | Estado |
|---|---|---|
| Compose limpio | API, Ollama y Qdrant inician | Pendiente por release |
| Modelo descargado | POST /api/chat responde | Pendiente por hardware |
| Embeddings/Qdrant | Guarda y recupera recuerdos | Pendiente integración |
| Vosk instalado | STT español | Pendiente |
| Piper instalado | TTS reproduce audio | Pendiente |
| UI web | Chat desde navegador | Pendiente |
| Electron Linux | Ventana, bandeja y atajo | Pendiente |
| Electron Windows | Instalador y ejecución | Pendiente |
| Allowlist agente | Solo alias autorizados | Pendiente host real |
| Token incorrecto | Rechazo 401 | Parcialmente cubierto; falta manual |
| Captura manual | JPEG en sesión gráfica | Pendiente |
| Reinicio/restauración | Datos persisten y se recuperan | Pendiente |

## Comandos

~~~bash
python -m pytest -q
python -m compileall -q app desktop_agent tests
cd ui
npm ci
npm run lint
npm run build
~~~
