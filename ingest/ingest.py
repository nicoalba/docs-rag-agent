
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.config import (
    OPENAI_API_KEY, EMBEDDING_MODEL, PERSIST_DIR, DOCS_DIR, CHUNK_SIZE, CHUNK_OVERLAP
)

def main():
    os.makedirs(PERSIST_DIR, exist_ok=True)

    loader = DirectoryLoader(DOCS_DIR, glob="**/*.md", loader_cls=TextLoader, show_progress=True)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL)

    Chroma.from_documents(chunks, embedding=embeddings, persist_directory=PERSIST_DIR)
    print(f"Ingested {len(chunks)} chunks into {PERSIST_DIR}")

if __name__ == "__main__":
    main()
