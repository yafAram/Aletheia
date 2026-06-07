MODEL ?= llama3.2:3b
MSG ?= Hola Aletheia

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

pull-model:
	docker exec -it aletheia_ollama ollama pull $(MODEL)

list-models:
	docker exec -it aletheia_ollama ollama list

chat:
	curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"message":"$(MSG)"}'

health:
	curl http://localhost:8000/health
