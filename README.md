# Docs Q&A RAG — QuickNode Streams (WIP)

A small, portfolio-ready RAG app that answers questions about **QuickNode Streams** with citations.

**Stack:** FastAPI (API), LangChain + **Chroma** (vector store), Streamlit (UI).  
**Status:** UI deployed on Render; retrieval runs from a persistent Chroma DB (`data/db`).

---

## Live Demo
- **UI:** https://docs-rag-agent.onrender.com
- **API:** (add your API URL here when deployed)

> The UI reads the API base from the `API_URL` environment variable.

---

## TL;DR
- **Local dev:** Docker Compose *or* Python venv.
- **Docs source:** QuickNode Streams pages crawled and embedded directly into **Chroma** at `data/db/`.
- **`data/docs/` can be empty.** It’s only used if you choose to ingest local Markdown.
- **UI on Render:** built with `dockerfile.ui`. Set `API_URL` to point at your public API.

---

## Project Layout
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
│  ├─ docs/              # optional; can be empty (keep the folder present)
│  └─ db/                # Chroma DB (persisted)
├─ docker-compose.yml
├─ dockerfile.api        # API container
├─ dockerfile.ui         # UI container (Streamlit)
├─ requirements.txt
└─ .env.example
```

---

## Running Locally

### Option A — Docker Compose
```bash
docker compose up --build
# UI:  http://localhost:8501
# API: http://localhost:8000/docs
```

### Option B — Python (venv)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start API (port 8000)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, start UI (port 8501)
streamlit run ui/app.py --server.address 0.0.0.0 --server.port 8501
```

> If port 8000 is already in use (e.g., Docker running), use `--port 8001` and set `API_URL=http://localhost:8001` before starting the UI:
> ```bash
> export API_URL=http://localhost:8001
> streamlit run ui/app.py --server.port 8501
> ```

---

## Ingesting Docs (QuickNode Streams)

The crawler fetches only the Streams section and writes **straight into Chroma** (`data/db`).

```bash
# Example: run the crawler
python ingest/web_ingest_quicknode_streams.py

# Optional sanity check for your Chroma DB
python - <<'PY'
persist_dir="data/db"
import chromadb
try:
    client = chromadb.PersistentClient(path=persist_dir)  # chroma >= 0.5
except TypeError:
    from chromadb.config import Settings
    client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))

print("Collections:", [c.name for c in client.list_collections()])
coll = client.get_collection(name="docs")  # adjust if you used a different name
print("Count:", coll.count())
sample = coll.get(limit=3, include=["documents","metadatas","ids"])
for i,(doc,meta,_id) in enumerate(zip(sample["documents"], sample["metadatas"], sample["ids"]),1):
    print(f"--- sample {i} ---")
    print("source:", (meta or {}).get("source"))
    print((doc or "")[:200], "…")
PY
```

**Notes**
- You’ll see `chroma.sqlite3` and several `.bin` files under `data/db/` — that’s normal (Chroma index + catalog).
- Keep `data/docs/` **present but empty** unless you want to ingest local Markdown.

---

## Deploying the **UI Only** on Render

You already have a UI-only Dockerfile: **`dockerfile.ui`** (Streamlit on port 8501).

1. **Render → New → Web Service**  
2. Connect this repo → **Environment: Docker**  
3. **Dockerfile path:** `dockerfile.ui`  
4. **Port:** `8501`  
5. **Environment Variable:**  
   - `API_URL` = `https://<your-api-service>.onrender.com` (full HTTPS URL, no trailing slash)  
6. **Create Web Service** and wait for it to build.  
7. Visit the Render URL and ask a question.

> **Updating UI text?** Commit & push changes, then in Render: **Manual Deploy → Clear build cache & deploy**, and hard-refresh the page (Ctrl/Cmd+Shift+R).

### Adjusting an env var on an existing Render service
- Open your UI service → left sidebar **Environment** → add/edit `API_URL` → **Save** → **Manual Deploy → Clear build cache & deploy**.

---

## Deploying the API (Optional, for a full public demo)

Use **`dockerfile.api`** (FastAPI on port 8000). **Important:** current code references **Ollama** (`ChatOllama`, `OllamaEmbeddings`). Render does not run an Ollama server by default.

Two ways forward:
1. **Switch to a hosted LLM** (easiest):
   - Update `app/chains.py` to use `langchain_openai` (or Together/Groq).
   - Set the relevant API key(s) via env vars.
2. **Host an Ollama-compatible endpoint** elsewhere and point your API to it via env.

After the API is live, set the UI’s `API_URL` to the API’s Render URL and redeploy the UI.

Add CORS in FastAPI so the UI can reach it:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://<your-ui>.onrender.com"],  # your Render UI URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Configuration

- **UI**
  - `API_URL` — where the Streamlit UI sends requests.  
    - Local default: `http://localhost:8000`  
    - On Render: set to your API’s public URL (`https://<api>.onrender.com`)

- **API**
  - `CHROMA_DIR` — path to Chroma’s persistent store (default: `data/db`).  
  - `CHROMA_COLLECTION` — collection name (default: `docs`).

---

## Common Troubleshooting

- **UI shows old text on Render**  
  You didn’t redeploy from the latest commit. Push changes → **Manual Deploy → Clear build cache & deploy** → hard refresh.

- **`NameResolutionError: 'docs-rag'` in the UI**  
  `API_URL` is wrong (e.g., pointing to a docker-compose hostname). Use a full public URL with scheme, like `https://<api>.onrender.com`.

- **`HTTPConnectionPool(host='api', port=8000)` / timeouts**  
  API container isn’t reachable. Check `docker compose logs -f api`. Ensure `ports: - "8000:8000"` is set and the server binds `0.0.0.0`.

- **Deleting `data/docs` breaks the app**  
  Your compose or code expects the path. Keep an empty folder:
  ```bash
  mkdir -p data/docs && touch data/docs/.gitkeep
  ```
  Or remove the mount and guard any `DirectoryLoader` usage.

- **Uvicorn: “address already in use”**  
  Another process (often Docker) is on port 8000. Use `--port 8001` locally or stop the container.

- **LangChain deprecation warnings**  
  Consider migrating to:
  ```python
  from langchain_chroma import Chroma
  from langchain_ollama import ChatOllama, OllamaEmbeddings
  ```
  and update `requirements.txt` accordingly.

---

## Understanding `data/db/` (Chroma)

- `chroma.sqlite3` — catalog of collections and records (metadata).  
- index shards / `.bin` files — ANN index storing your embeddings.  
- Retrieval queries by similarity and returns chunks + `source` metadata for citations.

---

## Future Work
- Swap Ollama for a hosted LLM to make API cloud-friendly.
- Add a tiny `/health` route and request tracing.
- Optional: export Chroma docs to Markdown for auditability.
- Add RAG evals (RAGAS) on a small Q/A set for Streams.
- Re-ranking (Cohere/ColBERT), caching, stronger injection defenses.

---

MIT Licensed. Built for portfolio use.
