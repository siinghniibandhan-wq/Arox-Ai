#!/bin/bash
set -e

echo "=== Booting Local Edge Mode (Consumes ONLY your RAM & Local Storage) ==="

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️ Please fill in your AWS_POSTGRES_HOST and credentials in .env before running!"
    exit 1
fi

echo "1. Spinning up local engine containers..."
docker compose -f docker-compose.local.yml up -d

echo "2. Loading local quantized weights (qwen2.5:7b) into Ollama..."
docker exec -it local_llm_engine ollama pull qwen2.5:7b

echo "=== Local Hardware Engine Live! ==="
echo "Local API listening on: http://localhost:8001"
echo "Ollama listening on:     http://localhost:11434"
echo "State synced to:        AWS PostgreSQL"
