# Operación y diagnóstico

## Servicios

~~~bash
docker compose ps
docker compose logs -f --tail=100 api
docker compose logs -f --tail=100 ollama
docker compose logs -f --tail=100 qdrant
curl -fsS http://127.0.0.1:8000/health
~~~

Health confirma que FastAPI responde, no que Ollama, Qdrant o modelos estén listos.

## Ollama

~~~bash
docker exec -it aletheia_ollama ollama list
docker exec -it aletheia_ollama ollama show llama3.2:3b
docker exec -it aletheia_ollama ollama pull llama3.2:3b
docker exec -it aletheia_ollama ollama pull nomic-embed-text
~~~

## Qdrant

~~~bash
curl -fsS http://127.0.0.1:6333/collections
~~~

La colección se inicializa al primer uso de memoria. La dimensión debe coincidir con el modelo de embeddings.

## Permisos storage en Linux

Haz copia antes de cambiar propietarios. El contenedor admite ALETHEIA_UID/ALETHEIA_GID:

~~~bash
export ALETHEIA_UID="$(id -u)"
export ALETHEIA_GID="$(id -g)"
docker compose up -d --build api
~~~

No borres archivos *.corrupt-* sin respaldarlos y revisar su contenido.

## Token del agente

El token suele estar en ~/.config/aletheia/desktop-agent-token.

~~~bash
TOKEN="$(cat ~/.config/aletheia/desktop-agent-token)"
curl -fsS -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8765/v1/apps
unset TOKEN
~~~

No imprimas ni compartas el token. Si hay un agente antiguo en el puerto 8765, ciérralo antes de iniciar otra instancia.

## Piper sin modelo

La configuración espera un par .onnx y .onnx.json:

~~~bash
find models/piper -maxdepth 1 -type f -printf '%f\n'
docker exec aletheia_api sh -lc 'ls -lah /app/models/piper'
~~~

Instala un modelo compatible y actualiza ambas rutas en .env. No renombres un modelo distinto.

## Captura de pantalla

Requiere mss, Pillow y una sesión gráfica activa. En un servidor sin display no estará disponible. La captura es manual y no persistente.

## Respaldos

~~~bash
cp -a storage "storage.backup.$(date +%Y%m%d-%H%M%S)"
cp .env .env.backup
~~~

No uses docker compose down -v durante mantenimiento normal: elimina volúmenes persistentes.
