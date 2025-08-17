
from typing import List
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.docstore.document import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

from .config import (
    OPENAI_API_KEY, EMBEDDING_MODEL, LLM_MODEL, PERSIST_DIR, DOCS_DIR, 
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K
)

def get_retriever():
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL)
    vectordb = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    return vectordb.as_retriever(search_kwargs={"k": TOP_K})

_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful technical assistant. Use the context to answer. Cite sources as [source: <path or url>]. If unsure, say so."),
    ("human", "Question: {question}\n\nContext:\n{context}\n\nAnswer with citations.")
])

def format_docs(docs: List[Document]) -> str:
    lines = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        lines.append(f"[source: {src}]\n{d.page_content}")
    return "\n\n".join(lines)

def build_qa_chain():
    retriever = get_retriever()
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.1, openai_api_key=OPENAI_API_KEY)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | _prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever
