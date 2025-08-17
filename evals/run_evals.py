
import os, json
from typing import List, Dict
import pandas as pd

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from datasets import Dataset

from app.chains import build_qa_chain
from app.config import OPENAI_API_KEY, EMBEDDING_MODEL, PERSIST_DIR

def load_evalset(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def main():
    out_dir = "evals/out"
    os.makedirs(out_dir, exist_ok=True)

    chain, retriever = build_qa_chain()
    items = load_evalset("evals/dataset.jsonl")

    questions = [it["question"] for it in items]
    ground_truths = [it["ground_truth"] for it in items]

    answers, contexts = [], []
    for q in questions:
        docs = retriever.get_relevant_documents(q)
        ctx_texts = [d.page_content for d in docs]
        contexts.append(ctx_texts)
        answers.append(chain.invoke(q))

    ds = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })

    result = evaluate(
        ds,
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.0, openai_api_key=OPENAI_API_KEY)
    )

    df = result.to_pandas()
    df.to_csv(f"{out_dir}/metrics.csv", index=False)
    with open(f"{out_dir}/metrics.md", "w", encoding="utf-8") as f:
        f.write("# RAGAS Metrics\n\n")
        f.write(df.to_markdown(index=False))

    print("Wrote evals to:", out_dir)

if __name__ == "__main__":
    main()
