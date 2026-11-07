# Agente de escritorio

## Propósito
Proceso local separado de la API principal. Se ejecuta en la sesión gráfica del host porque un contenedor no tiene acceso automático a las ventanas del usuario.

## Rutas implementadas
- GET /health: estado del proceso.
- GET /v1/apps: lista alias permitidos (Bearer).
- POST /v1/apps/open: abre alias permitido (Bearer).
- POST /v1/browser/open: abre URL HTTP/HTTPS (Bearer).
- POST /v1/screen/capture: captura manual JPEG de pantalla primaria (Bearer).

La UI Electron actual integra health, listado y apertura de apps. Navegador y captura aún no están conectados al puente IPC.

## Seguridad
- Host default 127.0.0.1; puerto 8765.
- Bearer token para acciones.
- Token compartido normalmente en ~/.config/aletheia/desktop-agent-token.
- Allowlist de alias y argumentos.
- subprocess con shell=False.
- No acepta comandos de shell, teclado o ratón arbitrarios.
- Captura puntual; no graba ni guarda la imagen en disco.

## Instalar

Linux:
~~~bash
python3.11 -m venv .venv-desktop
source .venv-desktop/bin/activate
pip install -r desktop_agent/requirements.txt
python -m desktop_agent
~~~

Windows PowerShell:
~~~powershell
py -3.11 -m venv .venv-desktop
.\.venv-desktop\Scripts\Activate.ps1
pip install -r desktop_agent\requirements.txt
python -m desktop_agent
~~~

Dependencias: FastAPI, Uvicorn, mss y Pillow. Lumina intenta iniciar el agente desde .venv-desktop.

## Allowlist
~~~bash
export ALETHEIA_DESKTOP_ALLOWED_APPS='{"editor":["code"],"files":["thunar"]}'
~~~

Cada valor es una lista de argumentos; no agregues shell ni comandos compuestos.

## Comprobar
~~~bash
curl http://127.0.0.1:8765/health
TOKEN="$(cat ~/.config/aletheia/desktop-agent-token)"
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8765/v1/apps
unset TOKEN
~~~

La captura requiere sesión gráfica y paquetes instalados. No es percepción visual continua. No expongas el agente a Internet ni a redes no confiables.
