# RAG chatbot

A small RAG app that answers questions about QuickNode Streams with citations. The content was crawled and ingested from [QuickNode docs](https://www.quicknode.com/docs/streams/getting-started) using a Python script.

## Tech stack

- FastAPI (back-end API)
- LangChain + Chroma (vector store)
- Streamlit (UI)
- Docker Compose (deployment)

## Quickstart: Run with Docker Compose

Deploy the app:

```bash
# from repo root
docker compose up -d --build
``` 

- UI: <http://localhost:8501>
- API: <http://localhost:8000/docs>

Verify it's running:

```bash
curl -sS http://localhost:8000/health || curl -I http://localhost:8000/docs
```

Docker commands:

```bash
docker compose restart ui
docker compose restart api
docker compose stop
docker compose down
# WARNING: this would delete named volumes (and your DB if you used one)
# docker compose down -v
```

>**Note**: First question may take longer while models warm up; subsequent queries are faster.

## Screenshot

![Docs RAG agent screenshot](images/docs-rag-screenshot.PNG)

## Ingest/update docs

This project stores content directly in Chroma at `data/db/` (you’ll see `chroma.sqlite3` and `.bin` shards). You can crawl more pages with the Python script:

```bash
python ingest/web_ingest_quicknode_streams.py
```

> **Note**: `data/docs/` is optional. Keep the folder (can be empty) so Docker binds it cleanly. Add `.md` files there only if you plan to run a separate ingest script that embeds them into Chroma.

## Project layout

```
docs-rag-agent/
├─ app/
│  ├─ main.py            # FastAPI app with /ask
│  ├─ chains.py          # embeddings, vectorstore, RAG chain
│  ├─ config.py
│  └─ __init__.py
├─ ui/
│  └─ app.py             # Streamlit client (reads API_URL env var)
├─ ingest/
│  ├─ web_ingest_quicknode_streams.py  # crawler → Chroma
│  └─ (optional) ingest_md.py          # local .md → Chroma
├─ data/
│  ├─ docs/              # optional; can be empty (keep folder present)
│  └─ db/                # Chroma DB (persisted)
├─ docker-compose.yml
├─ dockerfile.api        # API container
├─ dockerfile.ui         # UI container (Streamlit)
├─ requirements.txt
└─ .env
```

## Rerun 

Once the chatbot is built, use these cmds to bring it back up:

- *If you only clicked Stop (didn’t Delete) in Docker Desktop*:
  Just hit Play on the rag-chatbot stack. (CLI equivalent: `docker compose start`.)

- *If you changed code or Dockerfiles*:
  Use rebuild: `docker compose up -d --build`.

- *If you edited `.env` or `docker-compose.yml`*:
  Recreate so changes take effect: `docker compose up -d` (add `--force-recreate` if needed).

- *If you deleted containers (or ran down)*:
  Recreate them: `docker compose up -d` (add `--build` if code changed).

## Demo checks

Run `docker compose exec ollama ollama list`. If your model isn't listed, pull it:

```bash
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull llama3.1:8b
```
