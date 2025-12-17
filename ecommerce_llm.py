# ecommerce_llm.py
from dotenv import load_dotenv
load_dotenv()

import os
import time
import re
from typing import Optional
from xml.sax.saxutils import escape as xml_escape
from langsmith import traceable
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain_groq import ChatGroq

# local modules (adjust names if you named them differently)
from rag_store1 import get_retriever
from orders import get_order_status
from tools import search_products

# Prompt file
SYSTEM_PROMPT_FILE = "Bot_prompt.txt"
ECOMMERCE_KEYWORDS = [
    "buy", "price", "cost", "under", "recommend", "suggest",
    "show", "find", "search",
    "shoe", "shoes", "watch", "watches", "headphone", "headphones",
    "mobile", "phone", "laptop", "dress", "clothes", "jacket", "bag", "backpack",
    "discount", "deal", "offer", "sale",
    "return", "refund", "policy", "delivery", "shipping"
]

SMALL_TALK_KEYWORDS = [
    "hi", "hello", "hey", "hiii",
    "thank you", "thanks", "ok thanks",
    "ok", "okay","hi can you help me","hey are you there","thank you so much",
    "can you help", "help me",
    "good morning", "good evening","goodbye"
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
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

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
    
    @traceable(name="ecommerce_llm_process")
    def process(self, text: str) -> str:
        if not text or not text.strip():
            return "Please provide a query."

        lower = text.lower().strip()

    # --------------------------------------------------
    # 1️⃣ SMALL TALK / GREETINGS → LLM ONLY
    # --------------------------------------------------
        if any(k in lower for k in SMALL_TALK_KEYWORDS):
            try:
                resp = self.llm.invoke([
                    ("system", "You are a polite ecommerce assistant."),
                    ("human", text)
                ])
                return normalize_whitespace(strip_markdown(resp.content))
            except Exception:
                return "Hello 😊 I can help with products, orders, and return policies."

    # --------------------------------------------------
    # 2️⃣ ORDER TRACKING INTENT → TOOL
    # --------------------------------------------------
        if any(w in lower for w in [
            "track order", "order status","track my order" "where is my order","track",
            "track my order", "order update", "order id", "order #"
            ]):
            order_id = self._extract_order_id(text)
            if not order_id:
                return "Sure — please provide your order ID (for example ORD10023)."

            status = get_order_status(order_id)
            if not status:
                return f"I couldn't find an order with id `{order_id}`."

            reply = (
                f"Order {status['order_id']} is currently {status['status']}. "
                f"Placed on {status['placed_date']}. "
                f"Estimated delivery: {status['estimated_delivery']}. "
                f"Total: {status['total_amount']} {status['currency']}."
            )

            self.last_tool = {"type": "order_status", "result": status}
            self.last_retrieved = []
            return normalize_whitespace(reply)

    # --------------------------------------------------
    # 3️⃣ ECOMMERCE SEARCH INTENT → SEARCH + RAG
    # --------------------------------------------------
        if any(k in lower for k in ECOMMERCE_KEYWORDS):
            try:
                results = search_products(text, k=5)
            except Exception as e:
                print(f"[ecommerce_llm] search_products error: {e}")
                results = []

            self.last_tool = {"type": "search_products", "query": text, "results": results}

            structured_context = "\n".join([
                f"[{r.get('prod_id')}] {r.get('title')} | {r.get('final_price')} {r.get('currency')}"
                for r in results if r.get("prod_id")
                ]) or "No structured product results."

            docs = self.retriever.get_relevant_documents(text)
            self.last_retrieved = docs
            rag_docs_text = "\n\n".join(d.page_content for d in docs) if docs else ""

            combined_input = (
                f"User query: {text}\n\n"
            f"Products:\n{structured_context}\n\n"
            f"Reference docs:\n{rag_docs_text}\n\n"
            "Answer using ONLY the information above. "
            "Recommend at most 3 products."
        )

            resp = self.chain.invoke({"input": combined_input})
            out = resp.get("text") if isinstance(resp, dict) else str(resp)
            return normalize_whitespace(strip_markdown(out))

    # --------------------------------------------------
    # 4️⃣ NON-ECOMMERCE / OUT OF SCOPE
    # --------------------------------------------------
        return (
        "I can help with ecommerce-related questions like products, orders, "
        "returns, and delivery information. Please ask something related to shopping."
    )


