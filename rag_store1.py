# rag_store.py
import os
import json
import ast
from typing import List
import pandas as pd
from langsmith import traceable
from langchain.docstore.document import Document

# Handle LangChain import deprecation: prefer langchain_community if available
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
except Exception:
    # fallback for older installations
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import Chroma

CHROMA_DIR = "chroma_db"
HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # good default for demos

# --- Helpers to parse messy CSV fields ---
def safe_get(row, key):
    return str(row.get(key, "")).strip() if key in row else ""

def parse_number(value):
    if value is None:
        return ""
    s = str(value).strip()
    # remove common currency symbols and quotes
    s = s.replace('"', "").replace("'", "").replace("₹", "").replace("$", "")
    s = s.replace(",", "")
    try:
        if "." in s:
            return float(s)
        return int(s)
    except Exception:
        return s  # return raw if parsing fails

def parse_list_field(val):
    """
    Try to parse fields like:
    - '["Clothing","Shoes"]'
    - 'Clothing|Shoes'
    - 'Clothing, Shoes'
    Return list of trimmed strings.
    """
    if val is None:
        return []
    s = str(val).strip()
    if not s:
        return []
    # If it's a JSON array string
    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, (list, tuple)):
            return [str(x).strip() for x in parsed]
    except Exception:
        pass
    # If pipe-separated
    if "|" in s:
        return [p.strip() for p in s.split("|") if p.strip()]
    # If comma-separated
    if "," in s:
        return [p.strip() for p in s.split(",") if p.strip()]
    # fallback: single element
    return [s]

def build_product_content(row: pd.Series) -> str:
    # pick canonical fields
    title = safe_get(row, "title")
    brand = safe_get(row, "brand")
    desc = safe_get(row, "description")
    initial_price = parse_number(row.get("initial_price", ""))
    final_price = parse_number(row.get("final_price", ""))
    currency = safe_get(row, "currency")
    availability = safe_get(row, "availability")
    reviews_count = parse_number(row.get("reviews_count", ""))
    categories = parse_list_field(row.get("categories", ""))
    buybox_seller = safe_get(row, "buybox_seller")
    number_of_sellers = parse_number(row.get("number_of_sellers", ""))
    domain = safe_get(row, "domain")
    url = safe_get(row, "url")
    rating = parse_number(row.get("rating", ""))
    product_dimensions = safe_get(row, "product_dimensions")
    seller_id = safe_get(row, "seller_id")
    date_first_available = safe_get(row, "date_first_available")
    discount = safe_get(row, "discount")
    model_number = safe_get(row, "model_number")
    manufacturer = safe_get(row, "manufacturer")
    department = safe_get(row, "department")
    plus_content = safe_get(row, "plus_content")
    top_review = safe_get(row, "top_review")
    delivery = safe_get(row, "delivery")

    # Compose a readable document content for RAG (include important fields)
    parts = []
    if title:
        parts.append(f"Title: {title}")
    if brand:
        parts.append(f"Brand: {brand}")
    if desc:
        parts.append(f"Description: {desc}")
    if final_price != "":
        parts.append(f"Price: {final_price} {currency}")
    elif initial_price != "":
        parts.append(f"Price: {initial_price} {currency}")
    if availability:
        parts.append(f"Availability: {availability}")
    if rating != "":
        parts.append(f"Rating: {rating}")
    if reviews_count != "":
        parts.append(f"Reviews: {reviews_count}")
    if categories:
        parts.append(f"Categories: {', '.join(categories)}")
    if product_dimensions:
        parts.append(f"Dimensions: {product_dimensions}")
    if delivery:
        parts.append(f"Delivery info: {delivery}")
    if top_review:
        # keep top review but truncate if it's extremely long
        tr = top_review
        if len(tr) > 1500:
            tr = tr[:1500] + " ...[truncated]"
        parts.append(f"Top review: {tr}")
    # Add URL and seller info last (useful metadata)
    if url:
        parts.append(f"URL: {url}")
    if buybox_seller:
        parts.append(f"Buybox seller: {buybox_seller}")
    # join into final content
    content = "\n\n".join(parts)
    return content

def load_products_csv(csv_path: str = "products.csv") -> List[Document]:
    if not os.path.exists(csv_path):
        print(f"[rag_store] products CSV not found at {csv_path}")
        return []
    # read with pandas, try common separators and encoding
    try:
        df = pd.read_csv(csv_path, sep=None, engine="python", encoding="utf-8")
    except Exception:
        # fallback to default comma separator
        df = pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip")

    docs = []
    for idx, row in df.iterrows():
        # create an ID (prefer a column like sku/model_number) or fallback to row index
        prod_id = safe_get(row, "model_number") or safe_get(row, "seller_id") or safe_get(row, "title")[:60] or f"prod_{idx}"
        content = build_product_content(row)
        # metadata should include structured values so you can filter later
        meta = {
            "source": "products",
            "prod_id": prod_id,
            "title": safe_get(row, "title"),
            "brand": safe_get(row, "brand"),
            "final_price": str(parse_number(row.get("final_price", ""))),
            "currency": safe_get(row, "currency"),
            "availability": safe_get(row, "availability"),
            "url": safe_get(row, "url"),
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
    prod_docs = load_products_csv(csv_path)
    docs.extend(prod_docs)
    print(f"[rag_store] Loaded products: {len(prod_docs)}")

    faq_docs = load_faqs_json(faq_json_path)
    docs.extend(faq_docs)
    print(f"[rag_store] Loaded FAQs: {len(faq_docs)}")
    print(f"[rag_store] Total documents to index: {len(docs)}")

    # create or open Chroma DB
    vectordb = Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory=persist_directory)
    vectordb.persist()
    print(f"[rag_store] Persisted Chroma DB to '{persist_directory}'")
    return vectordb

@traceable(name="rag_retrieval")
def get_retriever(persist_directory: str = CHROMA_DIR, k: int = 4):
    embeddings = HuggingFaceEmbeddings(model_name=HF_EMBEDDING_MODEL)
    vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    return retriever

if __name__ == "__main__":
    build_vectorstore()
