# NovaMind AI Researcher — Streamlit UI + LangGraph pipeline
# Build: docker compose build   |   Run: see DOCKER.md and scripts/docker-deploy.sh

FROM python:3.11-slim-bookworm

# libsndfile: librosa/soundfile
# libcairo2-dev + build-essential: pycairo (xhtml2pdf → svglib → rlpycairo) has no wheel for slim; needs cc + cairo headers
# libcairo2: runtime for the built pycairo extension
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    libcairo2 \
    build-essential \
    pkg-config \
    libcairo2-dev \
    && pip install --upgrade pip \
    && pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt \
    && apt-get purge -y build-essential pkg-config libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 9501

# Streamlit health (1.28+)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9501/_stcore/health', timeout=5)" || exit 1

CMD ["streamlit", "run", "streamlitApp.py", \
     "--server.address=0.0.0.0", \
     "--server.port=9501", \
     "--server.fileWatcherType=none"]
