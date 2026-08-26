import httpx

r = httpx.post(
    "http://localhost:8000/v1/embeddings",
    json={}
)

assert r.status_code == 400, (
    f"expected 400 on CPU, got {r.status_code}"
)

assert "GPU" in r.json()["detail"]

print("GREEN CHECK: PASS")