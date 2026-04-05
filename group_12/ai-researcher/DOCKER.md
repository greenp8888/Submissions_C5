# Docker deployment (NovaMind AI Researcher)

This app is the **Streamlit** UI (`streamlitApp.py`). Images are **large** (~several GB) because `requirements.txt` includes PyTorch, sentence-transformers, and FAISS.

## File layout

| File | Purpose |
|------|---------|
| `Dockerfile` | Image build: Python 3.11, system libs, `pip install`, Streamlit on port **9501** |
| `docker-compose.yml` | Service **novamind**, ports, volumes, `.env` |
| `scripts/docker-deploy.sh` | Convenience commands: `build`, `up`, `down`, `logs`, etc. |
| `.dockerignore` | Keeps secrets and bulky local paths out of the build context |

**Note:** Docker Compose uses **YAML** (`.yml` / `.yaml`). There is no standard **`docker-compose.xml`** format for Compose v2; this repo ships `docker-compose.yml`.

---

## Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose V2](https://docs.docker.com/compose/) (`docker compose version`).
- At least **8 GB RAM** recommended for build/run (PyTorch + embeddings).

### Build details

- **PyTorch in the image is CPU-only** (installed from `download.pytorch.org/whl/cpu` before `requirements.txt`) so the Docker build does not pull NVIDIA CUDA wheels.
- **pycairo** (via `xhtml2pdf` → `svglib`) may build from source on Linux; the Dockerfile installs `build-essential`, `pkg-config`, and `libcairo2-dev` for that step, then removes the dev packages to keep the runtime image smaller. Runtime still ships **`libcairo2`** and **`libsndfile1`**.

---

## Quick start

From the `ai-researcher` directory:

```bash
cd ai-researcher
cp .env.example .env
# Edit .env: OPENROUTER_API_KEY or ANTHROPIC_API_KEY, TAVILY_API_KEY, optional Google OAuth

chmod +x scripts/docker-deploy.sh
./scripts/docker-deploy.sh build
./scripts/docker-deploy.sh up
```

Open **http://127.0.0.1:9501** (or your host IP).

The `up` command creates `.env` from `.env.example` if `.env` is missing.

---

## Manual Compose (without the script)

```bash
cp .env.example .env
# edit .env

docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
docker compose logs -f
```

Map a different **host** port to the container (Streamlit still listens on **9501** inside the image):

```bash
STREAMLIT_PORT=8080 docker compose up -d
```

---

## Volumes (persistence)

| Volume | Mount | Purpose |
|--------|--------|---------|
| `novamind_user_data` | `/app/user-data` | Chat JSON, uploads, artifacts |
| `novamind_hf_cache` | `/root/.cache/huggingface` | Embedding model cache |

Remove containers **and** data:

```bash
./scripts/docker-deploy.sh down-volumes
```

---

## Google OAuth behind Docker

1. In [Google Cloud Console](https://console.cloud.google.com/), add an **Authorized redirect URI** that matches how users reach the app, e.g. `https://your-domain.com/` (trailing slash must match `GOOGLE_OAUTH_REDIRECT_URI` in `.env`).
2. Set in `.env`:

   ```env
   GOOGLE_OAUTH_REDIRECT_URI=https://your-domain.com/
   ```

3. For **HTTPS** production, set `OAUTHLIB_INSECURE_TRANSPORT=0` in `docker-compose.yml` under `environment` (or pass via `.env` if you extend the compose file).

---

## Pushing the image to a registry

```bash
export DOCKER_REGISTRY=ghcr.io/your-org   # or docker.io/youruser
export IMAGE_TAG=v1.0.0                   # optional, default latest
./scripts/docker-deploy.sh push-image
```

Log in first: `docker login ghcr.io` (or your registry).

---

## Troubleshooting

- **Build OOM:** Increase Docker Desktop memory or build on a machine with more RAM.
- **First research run slow:** Sentence-transformers may download `EMBEDDING_MODEL` into the HF cache volume; subsequent runs are faster.
- **OAuth errors:** Redirect URI must exactly match Google Console and `.env`; use HTTPS in production with `OAUTHLIB_INSECURE_TRANSPORT=0`.
- **Health check failing:** Allow ~90s after start for imports; check logs: `./scripts/docker-deploy.sh logs`.

---

## Security

- Do **not** bake real API keys into the image. Use `.env` (gitignored) or your orchestrator’s secret store.
- Keep `user-data/` on a volume or encrypted disk in production.
