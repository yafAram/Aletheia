# Corrección de sincronización, memoria y permisos de Aletheia/Lumina

Este parche se basa en el ZIP del proyecto y en los logs compartidos. No borra `storage`, Qdrant ni modelos.

## Qué corrige

1. **Token compartido automático del agente**: el agente crea una única credencial en `~/.config/aletheia/desktop-agent-token` con permisos privados. Electron lee el mismo archivo; el agente vuelve a leerlo en cada petición, por lo que la rotación del archivo no exige volver a pegar el token en la UI. Lumina intenta iniciar el agente si `/health` no responde.
2. **Permisos de `storage`**: Compose puede ejecutar la API con el UID/GID del usuario Linux, evitando que nuevos JSON queden como `root:root` y modo `0600` inaccesible para el usuario de escritorio.
3. **Timeout de chat**: aumenta el timeout de la petición de escritorio a 5 minutos. Los logs mostraron generaciones reales de 99-113 segundos en CPU.
4. **Prompt más compacto y conversacional**: limita la cantidad de estado/memoria que se vuelve a inyectar al LLM y elimina la regla que dejaba el estilo prácticamente sin definir. No borra recuerdos almacenados.
5. **Captura de pantalla**: deja traceback en el log del agente si falla la sesión gráfica.

## Instalación segura

Desde la raíz del proyecto `~/Documentos/Aletheia`:

```bash
cd ~/Documentos/Aletheia
mkdir -p backups/antes-sincronizacion
cp -a docker-compose.yml backups/antes-sincronizacion/
cp -a app desktop_agent ui/desktop ui/src/desktop backups/antes-sincronizacion/
```

Copia los archivos de este ZIP conservando las rutas. Si usas Git, primero revisa `git status` y haz un commit/backup de tus cambios propios.

### Una sola migración de permisos

No elimines ni reemplaces `goals.json` ni ningún `*.corrupt-*`. Primero guarda una copia de `storage`:

```bash
cp -a storage "backups/storage-antes-permisos-$(date +%Y%m%d-%H%M%S)"
sudo chown -R "$(id -u):$(id -g)" storage
```

Esto cambia propietarios, no contenido. Después inicia Compose en la misma terminal para pasar el UID/GID correcto:

```bash
export ALETHEIA_UID="$(id -u)"
export ALETHEIA_GID="$(id -g)"
docker compose up -d --build api
```

No uses `docker compose down -v`.

### Token compartido

1. Cierra cualquier agente antiguo que hayas iniciado manualmente (Ctrl+C en esa terminal). Haz esto una sola vez para que no quede una instancia antigua ocupando el puerto 8765.
2. Cierra Lumina si está abierta.
3. Abre Lumina con:

```bash
source ~/.nvm/nvm.sh
cd ~/Documentos/Aletheia/ui
npm run desktop:dev
```

Lumina intentará iniciar el agente con `.venv-desktop/bin/python`. El agente generará el token compartido la primera vez. No pegues tokens manualmente en la interfaz ni publiques el archivo de token.

Si tu entorno virtual tiene otro nombre, ajusta el candidato Python en `ui/desktop/main.cjs` o crea `.venv-desktop` con `scripts/dev_install.sh` según el README del proyecto.

## Verificación

```bash
cd ~/Documentos/Aletheia
export ALETHEIA_UID="$(id -u)"
export ALETHEIA_GID="$(id -g)"
docker compose ps
curl -fsS http://127.0.0.1:8000/health
stat -c '%U:%G %a %n' storage storage/goals.json 2>/dev/null || true
stat -c '%U:%G %a %n' ~/.config/aletheia/desktop-agent-token
```

Para comprobar que el token compartido autentica, ejecuta desde la raíz del proyecto:

```bash
TOKEN="$(cat ~/.config/aletheia/desktop-agent-token)"
curl -fsS -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8765/v1/apps
unset TOKEN
```

## Diagnóstico importante

- Un `GET /health` del agente en `200` solo prueba que el proceso responde. No prueba que el token sea válido. La prueba real es `/v1/apps` autenticada.
- Los logs aportados muestran que Qdrant recibe búsquedas y escrituras correctamente. No incluyen una excepción de `goals.json`, por lo que la causa exacta de una corrupción de contenido no queda demostrada por esos logs. La propiedad root/permiso 0600 sí es una causa muy plausible de que el usuario anfitrión no pueda abrir el archivo.
- Si `goals.json` vuelve a contener JSON inválido después de aplicar esto, conserva el archivo `*.corrupt-*` y comparte salida de `stat storage storage/goals.json` y el mensaje exacto de `docker compose logs --tail=200 api`. No borres los respaldos.
- Piper seguirá sin voz hasta que exista un modelo compatible en `models/piper` montado en `/app/models/piper`. El log confirma que `es_MX-claude-high.onnx` no está en esa ruta. No se puede corregir el modelo ausente con permisos o tokens.
- El aviso GTK `font-antialiasing` y el aviso Wayland son del entorno gráfico de Electron; no explican la pérdida de memoria ni el timeout del LLM.

## Pruebas

El parche debe probarse en la máquina anfitriona con `npm run build` y `pytest`. No afirmamos que Electron esté validado en tu equipo hasta que esas pruebas y la verificación anterior pasen.
