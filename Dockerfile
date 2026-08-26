
FROM python:3.11-slim AS builder

WORKDIR /install


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt .


RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt



FROM python:3.11-slim AS runtime

WORKDIR /app


COPY --from=builder /install/deps /usr/local


COPY app/ .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]