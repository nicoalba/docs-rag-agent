
# Docs Q&A RAG (Blockchain-flavored) + Evals

**One polished, portfolio-ready project**: a small RAG app that answers questions about a local set of blockchain docs
(e.g., Solana/Anchor or EVM topics) with citations, plus **objective evals** (RAGAS) and **cost/risks** notes.

> Stack: FastAPI (backend), LangChain + Chroma (RAG), OpenAI (LLM/embeddings by default), Streamlit (UI), RAGAS (evals).

![screenshot](docs/screenshot-placeholder.png)

## TL;DR
- **Run locally** with Docker Compose or directly via Python.
- **Ask questions** in the Streamlit UI; see **source citations**.
- **Evaluate** your RAG quality with **RAGAS** on a small handcrafted dataset.
- Swap in Bedrock or other LLMs by editing `config.py`.

## Quickstart

### 1) Set environment
Copy `.env.example` to `.env` and fill in your keys.
```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=...
```

### 2) (Option A) Run with Docker Compose
```bash
docker compose up --build
# UI -> http://localhost:8501
# API -> http://localhost:8000/docs
```

### 2) (Option B) Run locally with Python
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1) Ingest docs into Chroma
python ingest/ingest.py

# 2) Start API
uvicorn app.main:app --reload --port 8000

# 3) In another terminal, start UI
streamlit run ui/app.py --server.port 8501
```

### 3) Ask questions
Open the Streamlit UI (`http://localhost:8501`), type a question like:
- *“What is an Anchor program account and how is it initialized?”*
- *“What’s the difference between PDAs and EVM contract addresses?”*

### 4) Run evals (RAGAS)
```bash
python evals/run_evals.py  # writes a report to evals/out/metrics.md
```

## Architecture

```mermaid
flowchart LR
  A[Docs (Markdown/HTML/PDF)] -->|Ingest & Chunk| B[Chroma Vector Store]
  B --> C[Retriever]
  C --> D[LangChain RAG Chain]
  E[User Question] --> D
  D -->|Answer + Citations| F[FastAPI /ask]
  F --> G[Streamlit UI]
  D --> H[Eval Harness (RAGAS)]
```

**Key pieces**
- **Ingest** (`ingest/ingest.py`): loads markdowns from `data/docs/`, chunks, embeds, and stores in **Chroma**.
- **API** (`app/main.py`): `/ask` returns an answer **with citations (source URLs/paths)**.
- **UI** (`ui/app.py`): minimalist Streamlit client with an input box and pretty citation rendering.
- **Evals** (`evals/run_evals.py`): evaluates faithfulness, answer relevancy, and context precision/recall on a small set.

## Evals & Results (example targets)
- **Faithfulness ≥ 0.75**, **Answer Relevancy ≥ 0.75** on `evals/dataset.jsonl`
- P50 latency ≤ 2.5s on laptop; **cost** ≤ $0.50 / 100 queries (documented in `docs/costs.md`)

> Edit the thresholds to match your hardware/model choice; include failures + planned fixes in `docs/limitations.md`.

## Security & Risk
- Limited to a **local, curated corpus** (no external browsing).
- Basic **prompt-injection** warning for suspicious inputs (see `app/guards.py`).
- No PII ingestion by default.

## Costs
- With `gpt-4o-mini` + `text-embedding-3-small`, a lightweight corpus typically costs **cents** per 100 queries.
- See `docs/costs.md` for the simple per-query math you can adapt to any model.

## Project Layout
```
docs-rag-qa/
├─ app/
│  ├─ main.py
│  ├─ chains.py
│  ├─ config.py
│  ├─ guards.py
│  └─ __init__.py
├─ ui/
│  └─ app.py
├─ ingest/
│  └─ ingest.py
├─ evals/
│  ├─ dataset.jsonl
│  ├─ run_evals.py
│  └─ out/  (generated)
├─ data/
│  ├─ docs/  (markdown seed corpus)
│  └─ db/    (Chroma index, generated)
├─ tests/
│  └─ test_smoke.py
├─ docs/
│  ├─ costs.md
│  ├─ limitations.md
│  └─ screenshot-placeholder.png
├─ .env.example
├─ requirements.txt
├─ docker-compose.yml
├─ Dockerfile.api
├─ Dockerfile.ui
├─ LICENSE
└─ CODE_OF_CONDUCT.md
```

## Limitations & Future Work
- This is a **local demo**; production needs auth, monitoring, rate limiting, tracing, and better evals.
- Add re-ranking (e.g., Cohere/ColBERT), caching, and more robust injection defenses.
- Swap Chroma for **pgvector** for a “production-ish” Postgres path.

---

MIT Licensed. Created as a quick-start portfolio project.

---

## Ingest a Single Section from a Live Docs Site (QuickNode Streams)

You can index only the **Streams** section from QuickNode docs:

```bash
# Install deps first (see requirements.txt)
python ingest/web_ingest_quicknode_streams.py
# This writes chunks to data/db and preserves original URLs for citations.
```

**Scope control:** The script starts at
`https://www.quicknode.com/docs/streams/getting-started` and keeps only pages
whose URL begins with `https://www.quicknode.com/docs/streams/` to avoid the rest
of the docs. Keep the crawl small while you iterate.
