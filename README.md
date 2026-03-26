# ChatApp (Streamlit + OpenRouter)

A chat application built with Streamlit, using OpenRouter for responses and conversation summaries.

## Features

- Multi-chat workflow with local file persistence (`chat_sessions/*.json`)
- Provider/model selection (OpenAI, Anthropic, Meta, Mistral)
- OpenRouter-backed chat completions
- Conversation summarization
- Chat export to `.txt` (metadata + summary + transcript)
- Dark/light theme support (CSS externalized under `styles/`)
- Responsive layout improvements for smaller screens

## Tech Stack

- Python 3.10+
- Streamlit
- python-dotenv
- OpenRouter API

## Project Structure

```text
build_chatapp/
|- main.py                 # Streamlit UI and app flow
|- openrouter_client.py    # OpenRouter HTTP client wrapper
|- storage.py              # Chat file persistence utilities
|- summaries.py            # Summary and export formatting logic
|- styles/
|  |- base.css             # Shared theme-aware styles
|  `- light.css            # Light-mode specific overrides
|- chat_sessions/          # Saved chat JSON files
|- .env.example
|- Makefile
|- requirements.txt
`- README.md
```

## Setup

1. Create and activate virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Configure environment variables.

- Copy `.env.example` to `.env`
- Add your API key:

```env
OPENROUTER_API_KEY=your_api_key_here
```

## Makefile Targets

The project includes a `Makefile` for common tasks.

```bash
make help
make setup
make run
make check
make clean
make reset-chats
```

Available targets:

- `make setup`: Create virtualenv and install dependencies
- `make venv`: Create `.venv`
- `make install`: Install dependencies into `.venv`
- `make run`: Start the Streamlit app
- `make check`: Run Python syntax checks
- `make clean`: Remove caches and bytecode
- `make reset-chats`: Delete saved chat JSON files

## Start / Stop / Access (Local)

### Start the project

Option A (Makefile):

```bash
make setup
make run
```

Option B (manual):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run main.py
```

### Access the project

After start, open:

- `http://localhost:8501`

### Stop the project

- In the terminal where Streamlit is running, press `Ctrl + C`.

## Local Deployment Notes

For local deployment on your machine:

1. Keep `.env` configured with `OPENROUTER_API_KEY`.
2. Run `make run` (or `streamlit run main.py`).
3. Use `http://localhost:8501` from your browser.

If you want to access from another device on the same network, run Streamlit with host binding and open firewall as needed:

```bash
streamlit run main.py --server.address 0.0.0.0 --server.port 8501
```

Then access via `http://<your-local-ip>:8501`.

## Extending to Web Deployment

To deploy this app on the web, you can package and host it on a platform that supports Python apps.

Typical path:

1. Keep dependency file (`requirements.txt`) updated.
2. Store secrets securely (never commit `.env`).
3. Set environment variable `OPENROUTER_API_KEY` in hosting provider config.
4. Use a process command similar to:
   - `streamlit run main.py --server.port $PORT --server.address 0.0.0.0`
5. Add basic auth/rate-limits if exposing publicly.

Common hosting options:

- Streamlit Community Cloud (quickest for Streamlit apps)
- Render / Railway / Fly.io
- Container-based deployment (Docker + any cloud VM or Kubernetes)

## Data Storage

- Chats are stored in `chat_sessions/`.
- Writes are atomic (temp file + replace) to reduce corruption risk.
- Malformed chat files fall back to defaults.

## Error Handling

- OpenRouter calls use a shared client with timeout/error mapping.
- Summary generation falls back to local summary text when API calls fail.

## Known Behavior

- `ðŸ‘` / `ðŸ‘Ž` are currently visual indicators only; they do not alter model behavior.
