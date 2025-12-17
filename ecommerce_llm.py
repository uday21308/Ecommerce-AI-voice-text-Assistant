# ecommerce_llm.py
from dotenv import load_dotenv
load_dotenv()
import os
import time
import re
from typing import Optional
from xml.sax.saxutils import escape as xml_escape
from langsmith import traceable
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from rag_store1 import get_retriever
from orders import get_order_status, create_order
from tools import search_products
from returns import get_return_by_order, create_return_request

SYSTEM_PROMPT_FILE = "Bot_prompt.txt"
PLACE_ORDER_KEYWORDS = [
    "place order", "order now", "buy now",
    "i want to buy", "purchase", "order this",
    "place an order"
]
ECOMMERCE_KEYWORDS = [
    "buy", "price", "cost", "under", "recommend", "suggest",
    "show", "find", "search",
    "shoe", "shoes", "watch", "watches", "headphone", "headphones",
    "mobile", "phone", "laptop", "dress", "clothes", "jacket", "bag", "backpack",
    "discount", "deal", "offer", "sale",
    "return", "refund", "policy", "delivery", "shipping"
]
RETURN_KEYWORDS = [
    "return", "refund", "send back","return order",
     "want to return","how to return","refund my order"
    ]
SMALL_TALK_KEYWORDS = [
    "hi", "hello", "hey", "hiii",
    "thank you", "thanks", "ok thanks",
    "ok", "okay","hi can you help me","hey are you there","thank you so much",
    "can you help", "help me",
    "good morning", "good evening","goodbye"
]
FAQ_KEYWORDS = [
    "how can i", "how do i", "what is", "policy",
    "review", "rating", "feedback",
    "support", "contact",
    "payment", "refund",
    "account", "login"
]

# Order extraction regexes
ORDER_STRICT = re.compile(r"\bORD\d+\b", flags=re.IGNORECASE)    # matches ORD10009
ORDER_LOOSE = re.compile(r"(?:order\s*(?:#|id)?\s*[:#]?\s*)([A-Za-z0-9\-_]+)", flags=re.IGNORECASE)

def strip_markdown(s: str) -> str:
        return re.sub(r"\*\*(.*?)\*\*", r"\1", s)


def normalize_whitespace(s: str) -> str:
    """
    Collapse whitespace and convert line breaks into single spaces for plain-text output.
    Use this for UI/TTS plain-text channel (so JSON doesn't contain '\n').
    """
    if not s:
        return s
    # convert CRLF to LF
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # collapse multiple newlines into one
    s = re.sub(r"\n{2,}", "\n", s)
    # replace remaining newlines with a single space
    s = s.replace("\n", " ")
    # collapse multiple spaces
    s = re.sub(r"[ \t]+", " ", s).strip()
    return s

def text_to_ssml(text: str, lang: str = "en-US", break_ms: int = 350) -> str:
    """
    Convert plain/multiline text into simple SSML:
     - escape XML special chars
     - paragraphs (double newlines) -> <p>..</p>
     - single newlines -> <break time="Xms"/>
     - wrap in <speak> with lang
    Keep it conservative so it works with most TTS engines.
    """
    if not text:
        return "<speak></speak>"

    # normalize CRLF
    t = text.replace("\r\n", "\n").replace("\r", "\n")

    # split into paragraphs on blank line(s)
    paragraphs = re.split(r"\n\s*\n", t)

    ssml_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # within paragraph, treat single newlines as short pauses
        lines = p.split("\n")
        # escape XML chars for safety
        escaped_lines = [xml_escape(line.strip()) for line in lines if line.strip()]
        # join lines with small break
        if len(escaped_lines) == 1:
            ssml_p = escaped_lines[0]
        else:
            br = f'<break time="{break_ms}ms"/>'
            ssml_p = br.join(escaped_lines)
        # wrap paragraph
        ssml_parts.append(f"<p>{ssml_p}</p>")

    ssml_body = "\n".join(ssml_parts)
    # final SSML (with lang)
    ssml = f'<speak xml:lang="{xml_escape(lang)}">{ssml_body}</speak>'
    return ssml

class EcommerceLLM:
    def __init__(self, model_name: str = "llama-3.1-8b-instant", temperature: float = 0.0, retriever_k: int = 4):
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY missing in environment")

        # LLM
        self.llm = ChatGroq(temperature=temperature, model_name=model_name, groq_api_key=groq_key)

        # Memory for conversation (keeps short term chat history)
        self.memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True,k=2)

        # Load system prompt
        if not os.path.exists(SYSTEM_PROMPT_FILE):
            raise FileNotFoundError(f"{SYSTEM_PROMPT_FILE} not found. Create it with ecommerce instructions.")
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()

        # Single {input} variable to keep LangChain memory compatible
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])

        self.chain = LLMChain(llm=self.llm, prompt=self.prompt, memory=self.memory)

        # Retriever (Chroma)
        self.retriever = get_retriever(k=retriever_k)

        # placeholders for telemetry / debugging
        self.last_retrieved = None
        self.last_tool = None
        self.last_response_time_ms = None
            # inside EcommerceLLM class (paste after __init__)

    def text_to_ssml(self, text: str, lang: str = "en-US", break_ms: int = 350) -> str:
        """
        Instance wrapper for the module-level text_to_ssml helper so callers
        (e.g., FastAPI) can call llm.text_to_ssml(reply).
        """
        try:
            return text_to_ssml(text, lang=lang, break_ms=break_ms)
        except Exception as e:
            print(f"[ecommerce_llm] text_to_ssml error: {e}")
            # fallback to minimal safe SSML
            safe = xml_escape(normalize_whitespace(strip_markdown(text or "")))
            return f'<speak xml:lang="{xml_escape(lang)}"><p>{safe}</p></speak>'


    def _extract_order_id(self, text: str) -> Optional[str]:
        """Try multiple strategies to extract an order id like ORD12345 from free text."""
        # 1) strict pattern (fast, reliable)
        m = ORDER_STRICT.search(text)
        if m:
            return m.group(0).upper().strip()

        # 2) looser pattern (e.g., "order id ORD123" or "order: ORD123")
        m2 = ORDER_LOOSE.search(text)
        if m2:
            candidate = m2.group(1).strip().upper().strip(".,!?")
            if candidate:
                return candidate

        # 3) final fallback: scan tokens for one that looks like ORD### or has letters+digits
        tokens = re.findall(r"\b[A-Za-z0-9\-_]+\b", text)
        for t in tokens:
            if t.upper().startswith("ORD") and any(ch.isdigit() for ch in t):
                return t.upper().strip()
        return None
    
    def _extract_quantity(self, text: str) -> Optional[int]:
        m = re.search(r"\b(\d+)\b", text)
        if m:
            return int(m.group(1))
        return 1


    @traceable(name="ecommerce_llm_process")
    def process(self, text: str) -> str:
        if not text or not text.strip():
            return "Please provide a query."

        lower = text.lower().strip()

        # --------------------------------------------------
        # 1️⃣ SMALL TALK
        # --------------------------------------------------
        if any(k in lower for k in SMALL_TALK_KEYWORDS):
            try:
                resp = self.llm.invoke([
                    ("system", "You are a polite ecommerce assistant."),
                    ("human", text)
                ])
                return normalize_whitespace(strip_markdown(resp.content))
            except Exception:
                return "Hello 😊 I can help with products, orders, and returns."
            
        # --------------------------------------------------
        # 2️⃣ RETURN / REFUND INTENT
        # --------------------------------------------------
        if any(k in lower for k in RETURN_KEYWORDS):

            order_id = self._extract_order_id(text)

            # ✅ CASE A: FAQ / POLICY QUESTION (NO ORDER ID)
            # Example: "How can I return an item?"
            if not order_id:
                docs = self.retriever.get_relevant_documents(text)
                self.last_retrieved = docs

                rag_text = "\n\n".join(d.page_content for d in docs) if docs else ""

                resp = self.chain.invoke({
                    "input": (
                        f"User question: {text}\n\n"
                        f"Return policy documents:\n{rag_text}\n\n"
                        "Answer clearly and concisely. "
                        "Do not ask for order ID unless the user wants to create a return."
                    )
                })

                out = resp.get("text") if isinstance(resp, dict) else str(resp)
                return normalize_whitespace(strip_markdown(out))

            # ✅ CASE B: RETURN ACTION (ORDER ID PRESENT)
            order = get_order_status(order_id)
            if not order:
                return f"I could not find order {order_id}. Please verify the order ID."

            # Optional but realistic check
            if order["status"].lower() != "delivered":
                return "Only delivered orders are eligible for return."

            existing = get_return_by_order(order_id)
            if existing:
                return normalize_whitespace(
                    f"A return already exists for order {order_id}. "
                    f"Status: {existing['Return_Status']}."
                )

            if "because" not in lower:
                return "Please tell me the reason for return (for example: damaged item, wrong size)."

            reason = text.split("because", 1)[1].strip()

            # ✅ Create return using ORDER DATA
            created = create_return_request(order, reason)

            self.last_tool = {"type": "create_return", "result": created}
            self.last_retrieved = []

            return normalize_whitespace(
                f"Your return request has been created successfully. "
                f"Order ID: {created['order_id']}. "
                f"Status: {created['Return_Status']}."
            )

        # --------------------------------------------------
        # 3️⃣ ORDER TRACKING INTENT
        # --------------------------------------------------
        if any(w in lower for w in [
            "track order",
            "order status",
            "where is my order",
            "track my order",
            "order update",
            "order id",
            "order #",
            "order status",
            "order details",
            "order info",
            "order information",
            "tell me about order",
            "where is my order",
            "track my order",
            "order update",
            "order id",
            "order #",
            "details of order"
        ]):
            order_id = self._extract_order_id(text)
            if not order_id:
                return "Sure — please provide your order ID (for example ORD10023)."

            status = get_order_status(order_id)
            if not status:
                return f"I couldn't find an order with id {order_id}."

            self.last_tool = {"type": "order_status", "result": status}
            self.last_retrieved = []

            return normalize_whitespace(
                f"Order {status['order_id']} is currently {status['status']}. "
                f"Placed on {status['placed_date']}. "
                f"Estimated delivery: {status['estimated_delivery']}. "
                f"Total: {status['total_amount']} {status['currency']}."
            )
        

        # ------------------ PLACE ORDER (NEW) ------------------
        if any(k in lower for k in PLACE_ORDER_KEYWORDS):
            qty = self._extract_quantity(text)
            if not qty:
                return "How many units would you like to order?"

            products = search_products(text, k=1)
            if not products:
                return "I could not find a matching product."

            product = products[0]

            order = create_order(
                product=product,
                quantity=qty,
                user_email="demo.user@email.com",
                user_name="Demo User"
            )

            self.last_tool = {"type": "create_order", "result": order}

            return (
                f"Your order has been placed successfully. "
                f"Order ID: {order['order_id']}. "
                f"Total: {order['total_amount']} {order['currency']}. "
                f"Expected delivery by {order['estimated_delivery']}."
            )
        
        # --------------------------------------------------
        # 4️⃣ PRODUCT / SEARCH INTENT
        # --------------------------------------------------
        if any(k in lower for k in ECOMMERCE_KEYWORDS):
            try:
                results = search_products(text, k=5)
            except Exception:
                results = []

            self.last_tool = {"type": "search_products", "query": text, "results": results}

            docs = self.retriever.get_relevant_documents(text)
            self.last_retrieved = docs

            structured_context = "\n".join(
                f"[{r['prod_id']}] {r['title']} | {r['final_price']} {r['currency']}"
                for r in results if r.get("prod_id")
            ) or "No products found."

            rag_docs_text = "\n\n".join(d.page_content for d in docs) if docs else ""

            resp = self.chain.invoke({
                "input": (
                    f"User query: {text}\n\n"
                    f"Products:\n{structured_context}\n\n"
                    f"Reference docs:\n{rag_docs_text}\n\n"
                    "Answer clearly and concisely."
                )
            })

            out = resp.get("text") if isinstance(resp, dict) else str(resp)
            return normalize_whitespace(strip_markdown(out))
        

        # --------------------------------------------------
        # 4️⃣ GENERIC FAQ / POLICY (RAG ONLY)
        # --------------------------------------------------
        if any(k in lower for k in FAQ_KEYWORDS):
            docs = self.retriever.get_relevant_documents(text)
            self.last_retrieved = docs
            self.last_tool = None

            rag_text = "\n\n".join(d.page_content for d in docs) if docs else ""

            if not rag_text:
                return "I don’t have that information right now. Please check our help center."

            resp = self.chain.invoke({
                "input": (
                    f"User question: {text}\n\n"
                    f"FAQ documents:\n{rag_text}\n\n"
                    "Answer clearly and concisely using only the documents."
                )
            })

            out = resp.get("text") if isinstance(resp, dict) else str(resp)
            return normalize_whitespace(strip_markdown(out))
        

        # --------------------------------------------------
        # 5️⃣ OUT OF SCOPE
        # --------------------------------------------------
        return (
            "I can help with ecommerce-related questions such as products, "
            "orders, returns, and delivery information."
        )
