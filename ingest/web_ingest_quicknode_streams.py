
# Ingest only QuickNode's "Streams" docs into the local vector store.
# Usage:
#   python ingest/web_ingest_quicknode_streams.py
#
# Notes:
# This script crawls starting from the Streams "Getting Started" page and only keeps pages whose URL starts with the Streams prefix. Citations will point back to the original URLs.
# Keep your crawl polite; respect robots.txt / TOS.


# ingest/web_ingest_quicknode_streams.py

import os
import re
import asyncio
from urllib.parse import urljoin, urldefrag

import aiohttp
from bs4 import BeautifulSoup

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# Pull project settings (chunking + DB path) from your config
try:
    from app.config import PERSIST_DIR, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
except Exception:
    # Fallbacks if config fields differ or aren’t present
    PERSIST_DIR = os.getenv("CHROMA_DIR", "data/db")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))

# --- Crawl scope (override via env if desired) ---
START_URL = os.getenv(
    "QNODE_START_URL",
    "https://www.quicknode.com/docs/streams/getting-started",
)
ALLOW_PREFIX = os.getenv(
    "QNODE_ALLOW_PREFIX",
    "https://www.quicknode.com/docs/streams/",
)
MAX_PAGES = int(os.getenv("QNODE_MAX_PAGES", "40"))
CONCURRENCY = int(os.getenv("QNODE_CONCURRENCY", "6"))
REQUEST_TIMEOUT = int(os.getenv("QNODE_REQUEST_TIMEOUT", "30"))

UA = "docs-rag-agent/0.1 (+https://example.local)"

# ---------------- Embeddings factory ----------------
def make_embeddings():
    """
    Prefer local/free Ollama embeddings when OLLAMA_BASE_URL is set,
    else fall back to OpenAI (requires OPENAI_API_KEY).
    """
    ollama = os.getenv("OLLAMA_BASE_URL", "").rstrip("/")
    if ollama:
        from langchain_community.embeddings import OllamaEmbeddings

        return OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=ollama)
    else:
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=os.getenv("OPENAI_API_KEY", ""))


# ----------------- HTML helpers ---------------------
def extract_links(base_url: str, html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: set[str] = set()
    for a in soup.select("a[href]"):
        href = a["href"]
        href = urljoin(base_url, href)
        href, _ = urldefrag(href)  # drop #fragment for dedupe
        if href.startswith(ALLOW_PREFIX):
            links.add(href)
    return links


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # prune obvious chrome
    for sel in ("nav", "header", "footer", "script", "style"):
        for t in soup.select(sel):
            t.decompose()
    text = soup.get_text("\n")
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text


# ----------------- Async crawler --------------------
async def fetch(session: aiohttp.ClientSession, url: str) -> tuple[str, str | None]:
    try:
        async with session.get(url, timeout=REQUEST_TIMEOUT) as r:
            ct = r.headers.get("Content-Type", "")
            if r.status != 200 or "text/html" not in ct:
                return url, None
            return url, await r.text()
    except Exception:
        return url, None


async def crawl() -> dict[str, str]:
    seen: set[str] = set()
    queue: list[str] = [START_URL]
    pages: dict[str, str] = {}

    conn = aiohttp.TCPConnector(limit_per_host=CONCURRENCY, ssl=False)
    async with aiohttp.ClientSession(
        headers={"User-Agent": UA}, connector=conn
    ) as session:
        sem = asyncio.Semaphore(CONCURRENCY)

        async def worker(u: str):
            async with sem:
                return await fetch(session, u)

        while queue and len(pages) < MAX_PAGES:
            batch: list[str] = []
            while queue and len(batch) < CONCURRENCY and len(pages) + len(batch) < MAX_PAGES:
                u = queue.pop(0)
                if u in seen:
                    continue
                seen.add(u)
                batch.append(u)

            results = await asyncio.gather(*[worker(u) for u in batch])
            for url, html in results:
                if not html:
                    continue
                pages[url] = html
                for l in extract_links(url, html):
                    if l not in seen:
                        queue.append(l)

    return pages


# ----------------- Entry point ----------------------
def main():
    print(f"[crawler] scope: prefix={ALLOW_PREFIX} start={START_URL} max_pages={MAX_PAGES}")
    pages = asyncio.run(crawl())
    print(f"[crawler] fetched: {len(pages)} pages")

    if not pages:
        print("[crawler] nothing fetched; aborting")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(CHUNK_SIZE),
        chunk_overlap=int(CHUNK_OVERLAP),
    )
    docs = []
    for url, html in pages.items():
        text = html_to_text(html)
        if not text:
            continue
        docs.append(Document(page_content=text, metadata={"source": url}))

    chunks = splitter.split_documents(docs)
    print(f"[ingest] chunks: {len(chunks)}; writing to {PERSIST_DIR}")

    os.makedirs(PERSIST_DIR, exist_ok=True)
    embeddings = make_embeddings()
    Chroma.from_documents(
        chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
    )
    print("[ingest] done.")


if __name__ == "__main__":
    main()
