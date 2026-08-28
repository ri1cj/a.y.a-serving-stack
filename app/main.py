import os
import torch
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

API_KEY = os.environ.get("API_KEY", "")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "256"))

app = FastAPI(title="complete serving stack")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class CompletionRequest(BaseModel):
    model: str
    messages: list
    max_tokens: int = 128
    require_gpu: bool = False

def require_api_key(authorization: str | None = Header(default=None)):
    if not API_KEY:
        return
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": os.environ.get("MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct")
    }

@app.get("/v1/models")
def list_models(authorization: str | None = Header(default=None)):
    require_api_key(authorization)
    return {
        "object": "list",
        "data": [{"id": os.environ.get("MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct"), "object": "model"}]
    }

@app.post("/v1/chat/completions")
def chat_completions(req: CompletionRequest, authorization: str | None = Header(default=None)):
    require_api_key(authorization)
    
    # Clamp max_tokens against MAX_TOKENS configuration
    effective_max_tokens = min(req.max_tokens, MAX_TOKENS)

    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": f"(on {DEVICE}) processed prompt with max_tokens={effective_max_tokens}"},
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": effective_max_tokens, "total_tokens": 10 + effective_max_tokens}
    }