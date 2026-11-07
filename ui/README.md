# Lumina UI

Cliente web y de escritorio de Aletheia, construido con React, TypeScript, Vite y Electron.

## Modos
- Web: npm run dev; carga la interfaz principal.
- Desktop: npm run desktop:dev; Electron carga la UI con ?desktop=1.

La API debe estar disponible en http://localhost:8000. En modo escritorio, Electron intenta iniciar el agente local desde .venv-desktop ubicado en la raíz del repositorio.

## Requisitos
- Node.js 22 LTS recomendado.
- npm.
- Backend iniciado.
- Para Desktop: Python 3.11 y dependencias de desktop_agent/requirements.txt.

## Desarrollo web
~~~bash
npm ci
npm run dev
~~~

## Desarrollo Electron
Desde la raíz prepara el agente:
~~~bash
python3.11 -m venv .venv-desktop
source .venv-desktop/bin/activate
pip install -r desktop_agent/requirements.txt
~~~

Luego:
~~~bash
cd ui
npm ci
npm run desktop:dev
~~~

## Validación
~~~bash
npm run lint
npm run build
~~~

## Empaquetado
- Linux AppImage: npm run package:linux
- Windows NSIS: npm run package:windows

Empaqueta y valida en el sistema destino.

## Seguridad
Electron usa preload e IPC limitado, contextIsolation, nodeIntegration deshabilitado y sandbox. No añadas acceso Node directo al renderer ni rutas arbitrarias al puente IPC.
