#!/usr/bin/env bash
set -e

echo "This script will create a local .env file for the project. It will NOT commit the file."

read -p "DEEPSEEK_API_KEY (leave empty to use mock analyzer): " DEEPSEEK_API_KEY
read -p "DEEPSEEK_API_URL [https://api.deepseek.com]: " DEEPSEEK_API_URL
DEEPSEEK_API_URL=${DEEPSEEK_API_URL:-https://api.deepseek.com}
read -p "OPENWEBUI_URL [http://localhost:3000]: " OPENWEBUI_URL
OPENWEBUI_URL=${OPENWEBUI_URL:-http://localhost:3000}

cat > .env <<EOF
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
DEEPSEEK_API_URL=${DEEPSEEK_API_URL}
OPENWEBUI_URL=${OPENWEBUI_URL}
EOF

echo ".env created. DO NOT commit this file."

read -p "Do you want to start the application with Docker Compose now? (y/N): " yn
yn=${yn:-N}
if [[ "$yn" =~ ^[Yy]$ ]]; then
  if command -v docker >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1 || command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "Starting docker compose..."
    # prefer `docker compose` if available, else `docker-compose`
    if docker compose version >/dev/null 2>&1; then
      docker compose up --build
    else
      docker-compose up --build
    fi
  else
    echo "Docker or docker-compose not found. Please start the app manually:"
    echo "  docker compose up --build"
  fi
else
  echo "Setup complete. Start the app manually with:" 
  echo "  docker compose up --build"
  echo "or run locally with venv:" 
  echo "  python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
fi
