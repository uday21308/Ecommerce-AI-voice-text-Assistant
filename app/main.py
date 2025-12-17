# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.deepgram_token import router as deepgram_router
import os

app = FastAPI(title="Ecommerce RAG API")


# ✅ ADD THIS CORS CONFIG
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="")
app.include_router(deepgram_router)

@app.get("/")
def root():
    return {"message": "Ecommerce RAG API. Check /health"}
