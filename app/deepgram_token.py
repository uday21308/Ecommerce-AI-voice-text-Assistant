from fastapi import APIRouter
import os
import time
import jwt

router = APIRouter()

@router.get("/deepgram/token")
def get_deepgram_token():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        return {"error": "Deepgram API key missing"}

    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 60,  # valid for 60 seconds
        "scope": "member"
    }

    token = jwt.encode(payload, api_key, algorithm="HS256")
    return {"token": token}
