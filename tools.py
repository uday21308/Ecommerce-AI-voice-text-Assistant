# tools.py
from typing import List, Dict
from rag_store import get_retriever
from langsmith import traceable

@traceable(name="product_search")
def search_products(query: str, k: int = 5) -> List[Dict]:
    """
    Returns structured product metadata using retriever (no LLM).
    Each item: {prod_id,title,brand,final_price,currency,availability,url,score?}
    """
    retriever = get_retriever(k=k)
    docs = retriever.get_relevant_documents(query)
    results = []
    for d in docs:
        md = d.metadata or {}
        if md.get("source") == "products":
            results.append({
                "prod_id": md.get("prod_id"),
                "title": md.get("title"),
                "brand": md.get("brand"),
                "final_price": md.get("final_price"),
                "currency": md.get("currency"),
                "availability": md.get("availability"),
                "url": md.get("url"),
            })
        else:
            results.append({"source": md.get("source"), "snippet": d.page_content[:300]})
    return results
