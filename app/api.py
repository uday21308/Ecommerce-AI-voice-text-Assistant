# app/api.py
from fastapi import APIRouter, Depends, HTTPException
from app.models import ChatRequest, ChatResponse
from app.deps import get_llm
import time
from fastapi import Query

router = APIRouter()

@router.get("/health")      
async def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, llm = Depends(get_llm)):
    import time
    if not req.text:
        raise HTTPException(status_code=400, detail="Empty `text` is not allowed")

    start = time.time()
    reply = llm.process(req.text)  # this returns clean plain text (no \n)
    elapsed = int((time.time() - start) * 1000)

    # build retrieved_docs
    retrieved = getattr(llm, "last_retrieved", None)
    retrieved_meta = None
    if retrieved:
        retrieved_meta = []
        for d in retrieved:
            md = d.metadata if hasattr(d, "metadata") else {}
            retrieved_meta.append({
                "source": md.get("source"),
                "prod_id": md.get("prod_id"),
                "title": md.get("title"),
                "final_price": md.get("final_price"),
                "url": md.get("url"),
            })

    last_tool = getattr(llm, "last_tool", None)

    # generate SSML for spoken responses
    try:
        # call helper on llm instance (we added text_to_ssml)
        reply_ssml = llm_text_to_ssml = getattr(llm, "text_to_ssml", None)
        if callable(reply_ssml):
            ssml = reply_ssml(reply)
        else:
            # fallback: simple wrapper if text_to_ssml not present
            from ecommerce_llm import text_to_ssml as global_text_to_ssml
            ssml = global_text_to_ssml(reply)
    except Exception as e:
        print(f"[api] SSML generation failed: {e}")
        ssml = None

    return ChatResponse(
        reply=reply,
        reply_ssml=ssml,
        retrieved_docs=retrieved_meta,
        last_tool=last_tool,
        elapsed_ms=elapsed
    )

@router.get("/search")
async def search(q: str = Query(..., min_length=1), k: int = Query(5, ge=1, le=20)):
    """
    Simple search endpoint — returns top-k product metadata from the vector DB (no LLM).
    Example: /search?q=running+shoes&k=5
    """
    from rag_store import get_retriever  # local import to avoid startup cost if unused
    retriever = get_retriever(k=k)
    docs = retriever.get_relevant_documents(q)
    results = []
    for d in docs:
        md = d.metadata or {}
        if md.get("source") == "products":
            results.append({
                "prod_id": md.get("prod_id"),
                "title": md.get("title"),
                "brand": md.get("brand"),
                "price": md.get("final_price"),
                "currency": md.get("currency"),
                "availability": md.get("availability"),
                "url": md.get("url"),
            })
        else:
            results.append({
                "source": md.get("source"),
                "snippet": d.page_content[:400]
            })
    return {"query": q, "k": k, "results": results}


# Add below other endpoints in app/api.py
@router.get("/orders/{order_id}")
async def get_order(order_id: str, email: str = Query(None, description="optional registered email to verify ownership")):
    """
    Returns order info for given order_id.
    If email is provided, we verify it matches the order's registered email before returning full details.
    If not provided, return minimal non-sensitive info (status and estimated delivery).
    """
    from orders import get_order_status
    order = get_order_status(order_id, user_email=email)
    if order is None:
        return {"found": False, "order_id": order_id, "message": "Order not found."}
    if isinstance(order, dict) and order.get("error") == "order_found_but_email_mismatch":
        return {"found": True, "order_id": order_id, "message": "Order found but provided email doesn't match. Provide the registered email to view details."}

    # If email provided and matched (or no email required), return full details
    if email:
        return {"found": True, "order": order}
    # If no email given, return minimal safe info
    return {
        "found": True,
        "order_id": order.get("order_id"),
        "status": order.get("status"),
        "estimated_delivery": order.get("estimated_delivery"),
        "placed_date": order.get("placed_date"),
    }