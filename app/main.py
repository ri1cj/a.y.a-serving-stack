import time
from fastapi import FastAPI
from transformers import AutoModelForCausalLM, AutoTokenizer
from schemas import (
    ModelCard,
    ModelList,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    ResponseMessage,
    Usage,
)
app = FastAPI()
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
print("Loading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
print("Model loaded successfully!")


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_ID}


@app.get("/v1/models", response_model=ModelList)
async def list_models():
    return ModelList(
        data=[ModelCard(id=MODEL_ID, created=int(time.time()), owned_by="owner")]
    )


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(req: ChatCompletionRequest):
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    encoded = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt", return_dict=True
    )

    inputs = encoded
    prompt_tokens = encoded["input_ids"].shape[1]

    max_new_tokens = req.max_tokens if req.max_tokens is not None else 128
    outputs = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)

    generated_ids = outputs[0][prompt_tokens:]
    completion_tokens = len(generated_ids)
    response_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

    return ChatCompletionResponse(
        id=f"chatcmpl-{int(time.time())}",
        created=int(time.time()),
        model=MODEL_ID,
        choices=[
            Choice(
                index=0,
                message=ResponseMessage(role="assistant", content=response_text),
                finish_reason="stop",
            )
        ],
        usage=Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )
# Cache invalidation test
