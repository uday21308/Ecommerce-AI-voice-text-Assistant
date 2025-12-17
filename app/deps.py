# app/deps.py
import os
from dotenv import load_dotenv
from ecommerce_llm import EcommerceLLM

load_dotenv()

_llm_instance = None

def get_llm():
    global _llm_instance
    if _llm_instance is None:
        # instantiate once (keeps memory)
        _llm_instance = EcommerceLLM()
    return _llm_instance
