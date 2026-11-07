# Fundamentos y decisiones de diseño

## Alcance de la investigación recuperada

El historial recuperable del proyecto documenta iteraciones técnicas, pruebas locales, revisión de logs y decisiones sobre ejecución local, memoria semántica, estado estructurado, personalidad configurable, objetivos explícitos, iniciativa limitada y agente de escritorio aislado.

No se recuperó una bibliografía académica concreta ni títulos/DOI de papers utilizados en aquellas conversaciones. Por rigor, no se atribuyen ideas a autores o artículos no verificables. Los enlaces al final son documentación técnica oficial de las tecnologías, no afirmaciones de que cada página sea la fuente académica original del diseño.

## Principios

### Local-first
El modelo de chat y embeddings corren mediante Ollama local; Qdrant puede ejecutarse en el mismo equipo. Reduce dependencia de inferencia remota. No significa que el sistema sea automáticamente seguro: puertos, permisos, logs y backups requieren controles.

### Recuperación semántica
Embeddings y búsqueda vectorial recuperan elementos relevantes en lugar de reenviar todo el historial. La calidad depende del modelo, consulta, metadatos y límites; no garantiza recordar todo ni reconstruir cronologías.

### Memoria y estado separados
Qdrant guarda recuerdos vectoriales; objetivos, iniciativa, personalidad, relaciones y estado propio tienen stores específicos. Así pueden probarse reglas deterministas sin iniciar servicios externos.

### Motores deterministas alrededor del LLM
Los motores producen señales estructuradas; el LLM redacta. La elegibilidad de objetivos, cooldown, estados y permisos permanece en código.

### Autonomía limitada y control humano
Iniciativa basada en observaciones, inactividad, cooldown y límites de pendientes. El usuario puede pausar, entregar o descartar. El agente solo ejecuta alias permitidos.

### Agente separado
La API dentro de Docker no comparte automáticamente la sesión gráfica del host. Un proceso local autenticado gestiona las acciones acotadas.

## Trade-offs

| Decisión | Motivo | Límite |
|---|---|---|
| Ollama local | Runtime/modelos intercambiables | Recursos locales |
| Qdrant | Búsqueda vectorial persistente | Servicio y dimensión compatibles |
| JSON stores | Simplicidad de MVP | Concurrencia/escala por validar |
| FastAPI | API tipada y OpenAPI | Seguridad adicional necesaria |
| React + Electron | Reutilizar UI web | Packaging por plataforma |
| Agente separado | Acceso a escritorio host | Token y allowlist |
| STT/TTS local | Evitar servicios de voz remotos | Modelos y dependencias adicionales |

## Referencias técnicas oficiales

- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- Ollama embeddings: https://ollama.com/blog/embedding-models
- Qdrant: https://qdrant.tech/documentation/
- Qdrant search: https://qdrant.tech/documentation/concepts/search/
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- Vosk: https://alphacephei.com/vosk/
- Piper: https://github.com/rhasspy/piper
- Electron security: https://www.electronjs.org/docs/latest/tutorial/security
- React: https://react.dev/learn
- Vite: https://vite.dev/guide/

## Investigación pendiente
- Evaluación de recuperación: precision@k, recall@k y relevancia humana.
- Memoria episódica/semántica y consolidación con evaluación reproducible.
- Consistencia de personalidad y prevención de antropomorfismo engañoso.
- Utilidad/frecuencia óptima de iniciativas.
- Amenazas y mitigaciones de agentes locales.
- Benchmark de latencia y RAM/VRAM por modelo y hardware.
