#!/usr/bin/env bash
# NovaMind AI Researcher — Docker helper (build / run / logs / optional registry push).
# Run from anywhere:  bash scripts/docker-deploy.sh up
# Or:                 cd "$(dirname "$0")/.." && ./scripts/docker-deploy.sh build

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
export COMPOSE_FILE

usage() {
  cat <<'EOF'
Usage: docker-deploy.sh <command> [args...]

Commands:
  build          Build the image (docker compose build)
  up             Create .env from .env.example if missing, then docker compose up -d
  down           Stop and remove containers (keeps volumes)
  down-volumes   Stop and remove containers + named volumes (deletes persisted chats/cache)
  logs           Follow container logs (pass extra args to docker compose logs)
  ps             docker compose ps
  restart        Restart the novamind service
  shell          Open bash inside the running container
  push-image     Tag and push image (requires DOCKER_REGISTRY, optional IMAGE_TAG)

Environment:
  STREAMLIT_PORT       Host port (default 9501)
  COMPOSE_FILE         Alternate compose file path
  DOCKER_REGISTRY      e.g. ghcr.io/myorg  (for push-image)
  IMAGE_TAG            default: latest

Note: Docker Compose uses YAML (docker-compose.yml), not XML.
EOF
}

ensure_env_file() {
  if [[ ! -f .env ]]; then
    if [[ -f .env.example ]]; then
      echo "[docker-deploy] No .env — copying .env.example -> .env"
      echo "[docker-deploy] Edit .env with your API keys and OAuth settings."
      cp .env.example .env
    else
      echo "[docker-deploy] ERROR: Missing .env and .env.example" >&2
      exit 1
    fi
  fi
}

cmd="${1:-up}"
shift || true

case "$cmd" in
  build)
    docker compose -f "$COMPOSE_FILE" build "$@"
    ;;
  up)
    ensure_env_file
    docker compose -f "$COMPOSE_FILE" up -d "$@"
    echo "[docker-deploy] Open http://127.0.0.1:${STREAMLIT_PORT:-9501}"
    ;;
  down)
    docker compose -f "$COMPOSE_FILE" down "$@"
    ;;
  down-volumes)
    docker compose -f "$COMPOSE_FILE" down -v "$@"
    ;;
  logs)
    docker compose -f "$COMPOSE_FILE" logs -f "$@"
    ;;
  ps)
    docker compose -f "$COMPOSE_FILE" ps "$@"
    ;;
  restart)
    docker compose -f "$COMPOSE_FILE" restart novamind "$@"
    ;;
  shell)
    docker compose -f "$COMPOSE_FILE" exec novamind bash
    ;;
  push-image)
    REGISTRY="${DOCKER_REGISTRY:?Set DOCKER_REGISTRY e.g. ghcr.io/myorg}"
    TAG="${IMAGE_TAG:-latest}"
    docker compose -f "$COMPOSE_FILE" build
    docker tag "novamind-ai-researcher:${TAG}" "${REGISTRY}/novamind-ai-researcher:${TAG}"
    docker push "${REGISTRY}/novamind-ai-researcher:${TAG}"
    echo "[docker-deploy] Pushed ${REGISTRY}/novamind-ai-researcher:${TAG}"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    usage
    exit 1
    ;;
esac
