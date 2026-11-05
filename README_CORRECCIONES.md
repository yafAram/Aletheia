# Correcciones focalizadas de Aletheia/Lumina

Este parche contiene cuatro archivos modificados. No incluye ni reemplaza `storage/`, modelos, `.env`, Docker volumes ni historial personal.

## Qué corrige

1. `GoalEngine`: elimina el patrón demasiado amplio que convertía peticiones conversacionales como “me gustaría saber más de ti” en objetivos persistentes. Conserva frases explícitas como “quiero desarrollar…” y “mi objetivo es…”.
2. `InitiativeAutonomyLoop`: evita acumular nuevas iniciativas autónomas mientras ya haya una pendiente sin entregar o descartar.
3. `desktop_agent/service.py`: registra la excepción real de captura de pantalla en el log local, sin exponer detalles internos al cliente HTTP.
4. `DesktopCompanion.tsx`: permite cambiar el token guardado y solo marca la conexión como configurada después de que la autenticación de listado de aplicaciones haya funcionado.

## Aplicación segura en Linux

Desde la raíz de tu repositorio `Aletheia`, primero crea una copia de los cuatro archivos:

```bash
mkdir -p backups/flujo-correcciones
cp app/modules/goal_engine.py backups/flujo-correcciones/
cp app/application/initiative_autonomy_loop.py backups/flujo-correcciones/
cp desktop_agent/service.py backups/flujo-correcciones/
cp ui/src/desktop/DesktopCompanion.tsx backups/flujo-correcciones/
```

Extrae el ZIP en una carpeta temporal y copia los cuatro archivos respetando sus rutas. Por ejemplo, si el ZIP está en la raíz del proyecto:

```bash
mkdir -p /tmp/aletheia-fix
unzip Aletheia_Flujo_Correcciones.zip -d /tmp/aletheia-fix
cp /tmp/aletheia-fix/Aletheia_Flujo_Correcciones/app/modules/goal_engine.py app/modules/goal_engine.py
cp /tmp/aletheia-fix/Aletheia_Flujo_Correcciones/app/application/initiative_autonomy_loop.py app/application/initiative_autonomy_loop.py
cp /tmp/aletheia-fix/Aletheia_Flujo_Correcciones/desktop_agent/service.py desktop_agent/service.py
cp /tmp/aletheia-fix/Aletheia_Flujo_Correcciones/ui/src/desktop/DesktopCompanion.tsx ui/src/desktop/DesktopCompanion.tsx
```

Ejecuta las pruebas del backend desde la raíz:

```bash
source .venv-desktop/bin/activate
python -m pytest tests/test_goal_and_initiative.py tests/test_goal_store_corruption.py tests/test_desktop_agent.py -q
```

Compila la interfaz:

```bash
cd ui
npm run build
cd ..
```

No uses `docker compose down -v`.

## Arranque por componentes

### 1. Docker (API, Ollama y Qdrant)

Desde la raíz del proyecto:

```bash
docker compose ps
docker compose up -d
docker compose ps
curl -fsS http://127.0.0.1:8000/health
```

`docker compose up -d` conserva los volúmenes. Si ya están activos y `/health` responde bien, no hace falta reiniciarlos.

### 2. Agente de escritorio

En una terminal independiente, desde la raíz del repositorio:

```bash
source .venv-desktop/bin/activate
export ALETHEIA_DESKTOP_HOST=127.0.0.1
export ALETHEIA_DESKTOP_PORT=8765
export ALETHEIA_DESKTOP_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
python -m desktop_agent
```

Deja esa terminal abierta. En otra terminal comprueba salud y autenticación, sin imprimir el token:

```bash
curl -fsS http://127.0.0.1:8765/health
curl -fsS -H "Authorization: Bearer $ALETHEIA_DESKTOP_TOKEN" http://127.0.0.1:8765/v1/apps
```

La segunda prueba debe ejecutarse en una terminal que tenga la misma variable de entorno que el agente. Si generas un token en una terminal diferente, no cambia el proceso ya iniciado.

Abre Lumina, entra en `Agente ⚙` y pega el token de la terminal del agente. Si hay un token antiguo guardado, usa `Cambiar token`. No compartas el token en capturas, logs ni chats. Como el token anterior se publicó en una conversación, rótalo.

### 3. Interfaz Electron

En otra terminal:

```bash
source ~/.nvm/nvm.sh
cd /ruta/a/Aletheia/ui
npm run desktop:dev
```

Sustituye `/ruta/a/Aletheia` por la ruta real de tu repositorio. No cierres la terminal del agente mientras usas las funciones de escritorio.

## Voz Piper: diagnóstico exacto

El error indica que la API dentro del contenedor busca un archivo que no encuentra. Comprueba qué modelos hay realmente:

```bash
docker exec aletheia_api sh -lc 'ls -lah /app/models/piper 2>&1'
find models/piper -maxdepth 1 -type f -printf '%f\n' 2>/dev/null
```

Si el archivo `es_MX-claude-high.onnx` no existe, no cambies la ruta a ciegas: configura `PIPER_MODEL_PATH` y `PIPER_CONFIG_PATH` en `.env` con los nombres reales de un modelo Piper compatible y su archivo `.json` correspondiente. Después recrea únicamente la API:

```bash
docker compose up -d --build api
```

No se puede recuperar la voz sin un modelo válido presente y montado en `/app/models/piper`.

## Captura de pantalla en Linux

El parche añade una traza de diagnóstico al log del agente. La captura manual depende de una sesión gráfica válida (X11/Wayland) y de los permisos del proceso. Si sigue dando 500, revisa la excepción de la terminal donde corre `python -m desktop_agent`. En una sesión sin escritorio gráfico la captura no estará disponible.

## Límite importante

El ZIP del proyecto no incluye `storage/goals.json`, por lo que no es posible diagnosticar el contenido exacto del archivo que se corrompió. El `GoalStore` del proyecto ya guarda mediante archivo temporal y reemplazo atómico, y preserva el archivo malformado con sufijo `.corrupt-*`. Antes de intentar recuperar datos, conserva todas las copias `storage/goals.json.corrupt-*`; no las borres ni las sobrescribas.
