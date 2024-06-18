# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt --no-cache-dir

EXPOSE 8000

CMD ["python", "app.py"]