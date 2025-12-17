# rag_store.py
import os, json
from typing import List
import pandas as pd
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

CHROMA_DIR = "chroma_db"
HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # fast, good for demos

def load_products_csv(csv_path: str = "products.csv") -> List[Document]:
    df = pd.read_csv(csv_path)
    docs = []
    for _, row in df.iterrows():
        # Build a single text blob containing all product fields
        content = (
            f"id: {row.get('id','')}\n"
            f"name: {row.get('name','')}\n"
            f"description: {row.get('description','')}\n"
            f"category: {row.get('category','')}\n"
            f"price: {row.get('price','')}\n"
            f"tags: {row.get('tags','')}\n"
            f"stock_status: {row.get('stock_status','')}\n"
        )
        meta = {
            "source": "products",
            "id": str(row.get("id", "")),
            "name": str(row.get("name", "")),
            "category": str(row.get("category", "")),
            "price": str(row.get("price", "")),
        }
        docs.append(Document(page_content=content, metadata=meta))
    return docs

def load_faqs_json(json_path: str = "faqs.json") -> List[Document]:
    docs = []
    if not os.path.exists(json_path):
        print(f"[rag_store] FAQ JSON not found at {json_path}; skipping.")
        return docs
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data.get("questions", [])
    for i, qa in enumerate(questions):
        q = qa.get("question", "").strip()
        a = qa.get("answer", "").strip()
        if not q and not a:
            continue
        content = f"Q: {q}\nA: {a}"
        meta = {"source": "faqs", "index": i, "question": q}
        docs.append(Document(page_content=content, metadata=meta))
    return docs

def build_vectorstore(csv_path: str = "products.csv", faq_json_path: str = "faqs.json", persist_directory: str = CHROMA_DIR):
    print("[rag_store] Building vector store...")
    embeddings = HuggingFaceEmbeddings(model_name=HF_EMBEDDING_MODEL)

    docs = []
    if os.path.exists(csv_path):
        docs.extend(load_products_csv(csv_path))
        print(f"[rag_store] Loaded products from {csv_path}: {len(docs)} docs (so far).")
    else:
        print(f"[rag_store] WARNING: {csv_path} not found.")

    faq_docs = load_faqs_json(faq_json_path)
    docs.extend(faq_docs)
    print(f"[rag_store] Total documents to index: {len(docs)}")

    # Create or open Chroma DB
    vectordb = Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory=persist_directory)
    vectordb.persist()
    print(f"[rag_store] Persisted Chroma DB to '{persist_directory}'")
    return vectordb

def get_retriever(persist_directory: str = CHROMA_DIR, k: int = 4):
    embeddings = HuggingFaceEmbeddings(model_name=HF_EMBEDDING_MODEL)
    vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    return retriever

if __name__ == "__main__":
    build_vectorstore()
