
# Ingest only QuickNode's "Streams" docs into the local vector store.
# Usage:
#   python ingest/web_ingest_quicknode_streams.py
#
# Notes:
# - This script crawls starting from the Streams "Getting Started" page and
#   only keeps pages whose URL starts with the Streams prefix.
# - Citations will point back to the original URLs.
# - Keep your crawl polite; respect robots.txt / TOS.

import os
from langchain_community.document_loaders import RecursiveUrlLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from app.config import (
    OPENAI_API_KEY, EMBEDDING_MODEL, PERSIST_DIR,
    CHUNK_SIZE, CHUNK_OVERLAP
)

START_URL = "https://www.quicknode.com/docs/streams/getting-started"
PREFIX = "https://www.quicknode.com/docs/streams/"

def main():
    loader = RecursiveUrlLoader(
        url=START_URL,
        max_depth=4,
        prevent_outside=True,
        use_async=True
    )
    raw_docs = loader.load()

    docs = [d for d in raw_docs if d.metadata.get("source", "").startswith(PREFIX)]

    # Deduplicate by URL
    seen = set()
    deduped = []
    for d in docs:
        src = d.metadata.get("source", "")
        if src and src not in seen:
            seen.add(src)
            deduped.append(d)
    docs = deduped

    if not docs:
        print("No Streams docs discovered; check START_URL and PREFIX.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)

    emb = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL)
    Chroma.from_documents(chunks, embedding=emb, persist_directory=PERSIST_DIR)

    print(f"Ingested {len(chunks)} chunks from {len(docs)} Streams pages into {PERSIST_DIR}.")

if __name__ == "__main__":
    main()
