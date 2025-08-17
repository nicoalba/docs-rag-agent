
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .chains import build_qa_chain
from .guards import is_suspicious

app = FastAPI(title="Docs Q&A RAG API")

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str

_chain, _retriever = build_qa_chain()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    if is_suspicious(req.question):
        raise HTTPException(status_code=400, detail="Question flagged as potentially unsafe. Please rephrase.")
    try:
        answer = _chain.invoke(req.question)
        return AskResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
