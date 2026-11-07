# Instalación de Aletheia

## Requisitos
- Docker Engine y Docker Compose plugin.
- Python 3.11.
- Node.js 22 LTS + npm para UI/Electron.
- Git y recursos suficientes para el modelo local.

## Backend con Compose

~~~bash
git clone https://github.com/yafAram/Aletheia.git
cd Aletheia
cp .env.example .env
export ALETHEIA_UID="$(id -u)"
export ALETHEIA_GID="$(id -g)"
docker compose up -d --build
docker compose ps
docker exec -it aletheia_ollama ollama pull llama3.2:3b
docker exec -it aletheia_ollama ollama pull nomic-embed-text
docker exec -it aletheia_ollama ollama list
curl http://127.0.0.1:8000/health
~~~

Swagger: http://127.0.0.1:8000/docs

El submódulo finanzas/nexo_fiance es independiente y no es necesario para ejecutar Aletheia. No inicialices submódulos si no lo necesitas.

## Backend nativo

Instala Ollama y Qdrant en el host. Configura OLLAMA_BASE_URL=http://127.0.0.1:11434 y QDRANT_URL=http://127.0.0.1:6333 en .env.

~~~bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
~~~

## UI web

~~~bash
cd ui
npm ci
npm run dev
~~~

## Lumina Desktop

Desde la raíz instala el agente:

Linux:
~~~bash
python3.11 -m venv .venv-desktop
source .venv-desktop/bin/activate
pip install -r desktop_agent/requirements.txt
~~~

Windows PowerShell:
~~~powershell
py -3.11 -m venv .venv-desktop
.\.venv-desktop\Scripts\Activate.ps1
pip install -r desktop_agent\requirements.txt
~~~

Después:

~~~bash
cd ui
npm ci
npm run desktop:dev
~~~

La API debe estar activa. Electron intenta iniciar el agente desde .venv-desktop.

## Voz

Los modelos no se incluyen en Git. Vosk requiere un directorio de modelo español bajo models/vosk; Piper requiere un archivo .onnx y su .onnx.json en models/piper. Configura las rutas internas del contenedor en .env y comprueba que ambos archivos existan.

## Empaquetado

Linux: cd ui && npm run package:linux  
Windows: cd ui && npm run package:windows

Construye y valida en el sistema operativo destino.
