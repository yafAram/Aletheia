# Matriz de pruebas MVP Lumina Desktop

| Caso | Resultado esperado | Estado |
|---|---|---|
| Electron inicia en modo desarrollo | Ventana transparente, sin marco, avatar visible | Por ejecutar en equipo destino |
| `GET /api/emotion` | Indicador API en línea | Por ejecutar |
| `POST /api/chat` | Mensaje y respuesta aparecen en el chat | Por ejecutar |
| `POST /api/tts/speak` | Reproducción de audio opcional | Por ejecutar con Piper configurado |
| `GET /health` agente | Indicador agente conectado | Por ejecutar |
| Token incorrecto | Mensaje de error, no abre aplicaciones | Por ejecutar |
| `GET /v1/apps` | Muestra solo aliases autorizados | Por ejecutar |
| `POST /v1/apps/open` | Abre alias autorizado | Por ejecutar |
| Atajo `Ctrl+Shift+L` | Muestra/oculta Lumina | Por ejecutar |
| Inicio automático | Se habilita/deshabilita desde la bandeja | Por ejecutar por plataforma |
| UI web original | Sigue disponible sin `?desktop=1` | Por ejecutar |
