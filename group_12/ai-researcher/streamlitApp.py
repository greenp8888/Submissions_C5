"""
NovaMind Deep Researcher — Streamlit chat UI (ChatGPT-style).

Run from the ``ai-researcher`` directory::

    # Use a venv and the SAME Python for pip + streamlit (PEP 668 / Homebrew Python).
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    which python
    which streamlit
    streamlit run streamlitApp.py

Both ``which`` paths must live under ``.venv/``. Run only the shell commands above; do not
paste explanatory words from docs as extra lines (the shell will report "command not found").

Uses the same LangGraph pipeline as ``app.py`` via ``streamlit_workflow.py``.

Sign-in is **Google OAuth** when **GOOGLE_OAUTH_CLIENT_ID** and **SECRET** are set; only
**@gmail.com** / **@googlemail.com** accounts are allowed. If OAuth is not configured, you can
**Log in as anonymous user** for local testing (data under ``user-data/anonymous_<id>/chats/``).

After Google login, chats persist under ``user-data/<sanitized_email>/chats/`` (gitignored),
where ``@`` and ``.`` in the email are replaced with ``_``.

Local file retrieval needs ``langchain-huggingface`` (listed in requirements.txt).

If startup fails with ``ModuleNotFoundError: torchvision``, install dependencies in this venv
(``torchvision`` is in ``requirements.txt``).

Many lines of ``Accessing __path__`` from ``transformers`` are warnings from Streamlit’s file
watcher; they are harmless once ``torchvision`` is installed. For a quieter console (no auto
reload on save), run: ``STREAMLIT_SERVER_FILE_WATCHER_TYPE=none streamlit run streamlitApp.py``
"""

from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote_plus

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from deep_researcher.config import ANTHROPIC_BUDGET_MODELS, LLM_PROVIDER_ANTHROPIC, LLM_PROVIDER_OPENROUTER

from streamlit_google_auth import (
    authorization_url,
    create_flow,
    create_signed_oauth_state,
    exchange_code_and_fetch_email,
    is_allowed_gmail,
    load_oauth_client_config,
    read_oauth_settings_from_env,
    sanitize_email_to_folder,
    verify_signed_oauth_state,
)
from streamlit_workflow import (
    derive_title,
    finalize_research_outputs,
    markdown_to_pdf_bytes,
    run_preflight,
    run_research,
    settings_from_ui,
    slug_filename_base,
    write_artifact_markdown,
)

load_dotenv()

ROOT = Path(__file__).resolve().parent
USER_DATA_ROOT = ROOT / "user-data"
BRAND_MARK_SVG = ROOT / "assets" / "novamind_mark.svg"

AUTH_FLASH_ERROR_KEY = "auth_flash_error"

_LOGOUT_KEYS = frozenset(
    {
        "user_email",
        "user_display_name",
        "user_folder",
        "chats_dir",
        "auth_anonymous",
        AUTH_FLASH_ERROR_KEY,
        "id",
        "title",
        "created_utc",
        "updated_utc",
        "question",
        "uploaded_paths",
        "messages",
        "human_preview_md",
        "preflight_trace_md",
        "status",
        "report_md",
        "gaps_md",
        "objective_md",
        "trace_md",
        "contradictions_md",
        "sources_detail_md",
        "evidence_records",
        "artifact_base_name",
        "artifact_dir",
        "enable_web_search",
        "top_k",
        "web_results_per_query",
        "max_research_rounds",
        "llm_provider",
        "openrouter_key",
        "openrouter_model",
        "anthropic_key",
        "anthropic_model",
    }
)
UPLOAD_FILE_TYPES: list[str] = [
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "webp",
    "gif",
    "bmp",
    "tif",
    "tiff",
    "mp3",
    "wav",
    "m4a",
    "flac",
    "ogg",
    "webm",
]

OPENROUTER_MODEL_PRESETS: list[str] = [
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    "openai/gpt-4-turbo",
    "anthropic/claude-3.5-haiku",
    "google/gemini-flash-1.5",
    "google/gemini-pro-1.5",
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-small-24b-instruct-2501",
    "deepseek/deepseek-chat",
]


def _hydrate_google_env_from_streamlit_secrets() -> None:
    try:
        s = st.secrets
        for key in ("GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET", "GOOGLE_OAUTH_REDIRECT_URI"):
            if key in s and str(s.get(key, "")).strip() and not os.environ.get(key, "").strip():
                os.environ[key] = str(s[key]).strip()
    except (FileNotFoundError, KeyError, AttributeError, TypeError, RuntimeError):
        return


def _build_oauth_client_pair() -> tuple[dict, str] | None:
    cid, sec, redir = read_oauth_settings_from_env()
    if not cid or not sec:
        return None
    return load_oauth_client_config(cid, sec, redir), redir


def _query_param_first(name: str) -> str | None:
    try:
        v = st.query_params.get(name)
    except Exception:
        return None
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        return str(v[0]).strip() if v else None
    s = str(v).strip()
    return s or None


def _set_auth_flash_error(message: str) -> None:
    """Persist sign-in errors across ``st.rerun()`` so the login page can show them."""
    st.session_state[AUTH_FLASH_ERROR_KEY] = (message or "").strip() or "Sign-in failed."


def _render_auth_flash_error_if_any() -> None:
    msg = st.session_state.pop(AUTH_FLASH_ERROR_KEY, None)
    if msg:
        st.error(msg)


def _clear_oauth_query_params() -> None:
    try:
        st.query_params.clear()
    except AttributeError:
        for k in list(st.query_params.keys()):
            try:
                del st.query_params[k]
            except Exception:
                pass


def get_chats_dir() -> Path:
    raw = st.session_state.get("chats_dir")
    if not raw:
        raise RuntimeError("Not signed in: chats_dir is unset.")
    return Path(raw)


def _setup_user_storage(email: str, display_name: str = "") -> None:
    folder = sanitize_email_to_folder(email)
    chats = USER_DATA_ROOT / folder / "chats"
    chats.mkdir(parents=True, exist_ok=True)
    st.session_state["user_email"] = email.strip().lower()
    st.session_state["user_display_name"] = display_name
    st.session_state["user_folder"] = folder
    st.session_state["chats_dir"] = str(chats.resolve())
    st.session_state.pop("auth_anonymous", None)


def _setup_anonymous_user() -> None:
    """Local testing only: random folder under user-data when Google OAuth is not configured."""
    aid = uuid.uuid4().hex
    folder = f"anonymous_{aid}"
    chats = USER_DATA_ROOT / folder / "chats"
    chats.mkdir(parents=True, exist_ok=True)
    st.session_state["user_email"] = f"anonymous+{aid[:12]}@local.test"
    st.session_state["user_display_name"] = "Anonymous (local test)"
    st.session_state["user_folder"] = folder
    st.session_state["chats_dir"] = str(chats.resolve())
    st.session_state["auth_anonymous"] = True


def logout_user() -> None:
    for k in list(st.session_state.keys()):
        if k in _LOGOUT_KEYS:
            st.session_state.pop(k, None)


def _oauth_client_secret(client_cfg: dict) -> str:
    return str((client_cfg.get("web") or {}).get("client_secret") or "").strip()


def _try_oauth_error_redirect() -> bool:
    """
    Google may redirect with ``error`` / ``error_description`` instead of ``code``.
    Capture that so the user sees it on the login screen after rerun.
    """
    err = _query_param_first("error")
    if not err:
        return False
    desc = unquote_plus(_query_param_first("error_description") or "").strip()
    parts = [f"Google returned **{err}**."]
    if desc:
        parts.append(desc)
    _set_auth_flash_error(" ".join(parts))
    _clear_oauth_query_params()
    st.rerun()
    return True


def _try_oauth_callback(client_cfg: dict, redirect_uri: str) -> bool:
    """
    If the URL contains OAuth ``code`` / ``state``, complete login and return True
    (caller should stop after rerun).
    """
    code = _query_param_first("code")
    state = _query_param_first("state")
    if not code or not state:
        return False
    secret = _oauth_client_secret(client_cfg)
    if not verify_signed_oauth_state(state, secret):
        _clear_oauth_query_params()
        _set_auth_flash_error(
            "Sign-in failed: invalid or expired session. Please try **Continue with Google** again."
        )
        st.rerun()
        return True
    try:
        email, name = exchange_code_and_fetch_email(client_cfg, redirect_uri, code)
    except Exception as e:
        _clear_oauth_query_params()
        _set_auth_flash_error(f"Google sign-in failed: {e}")
        st.rerun()
        return True
    if not is_allowed_gmail(email):
        _clear_oauth_query_params()
        _set_auth_flash_error(
            "Only personal Gmail accounts (**@gmail.com** or **@googlemail.com**) are allowed."
        )
        st.rerun()
        return True
    _clear_oauth_query_params()
    _setup_user_storage(email, name)
    st.rerun()
    return True


def _render_login_screen(client_cfg: dict, redirect_uri: str) -> None:
    _inject_layout_css()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        _render_brand_header()
        _render_auth_flash_error_if_any()
        st.markdown("## Sign in with Google")
        st.markdown(
            "Use a **@gmail.com** Google account. "
            "Legacy **@googlemail.com** addresses are treated as Gmail."
        )
        flow = create_flow(client_cfg, redirect_uri)
        signed_state = create_signed_oauth_state(_oauth_client_secret(client_cfg))
        url = authorization_url(flow, signed_state)
        st.link_button("Continue with Google", url, type="primary", use_container_width=True)
        st.caption(
            f"Your research chats are saved on this server under `{USER_DATA_ROOT.name}/` "
            "in a folder derived from your email."
        )


def _render_oauth_disabled_login_screen() -> None:
    """Shown when Google client id/secret are unset: optional anonymous test user."""
    _inject_layout_css()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        _render_brand_header()
        st.warning(
            "Google OAuth is not configured (**GOOGLE_OAUTH_CLIENT_ID** or "
            "**GOOGLE_OAUTH_CLIENT_SECRET** is missing)."
        )
        st.markdown(
            "Add credentials in `.env` or Streamlit **Secrets** to enable **Continue with Google**. "
            "For local testing you can continue without Google."
        )
        if st.button("Log in as anonymous user", type="primary", use_container_width=True):
            _setup_anonymous_user()
            st.rerun()
        st.caption(
            f"Creates a random profile and saves chats under `{USER_DATA_ROOT.name}/anonymous_<id>/chats/`. "
            "After **Sign out**, use this button again to start a different anonymous workspace."
        )
        with st.expander("Production OAuth setup"):
            st.markdown(
                "Set **GOOGLE_OAUTH_CLIENT_ID** and **GOOGLE_OAUTH_CLIENT_SECRET**. "
                "Optionally **GOOGLE_OAUTH_REDIRECT_URI** (default `http://localhost:8501/`). "
                "Register the redirect URI under *Authorized redirect URIs* in Google Cloud Console."
            )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_chat(chat_id: str) -> dict:
    short = chat_id.replace("-", "")[:8] or chat_id[:8]
    try:
        art_root = str(get_chats_dir())
    except RuntimeError:
        art_root = ""
    return {
        "id": chat_id,
        "title": f"Draft · {short}",
        "created_utc": _utc_now(),
        "updated_utc": _utc_now(),
        "question": "",
        "uploaded_paths": [],
        "messages": [],
        "human_preview_md": "",
        "preflight_trace_md": "",
        "status": "empty",
        "report_md": "",
        "gaps_md": "",
        "objective_md": "",
        "trace_md": "",
        "contradictions_md": "",
        "sources_detail_md": "",
        "evidence_records": [],
        "artifact_base_name": "",
        "artifact_dir": art_root,
        "enable_web_search": True,
        "top_k": 4,
        "web_results_per_query": 3,
        "max_research_rounds": 1,
        "llm_provider": LLM_PROVIDER_OPENROUTER,
        "openrouter_key": "",
        "openrouter_model": "openai/gpt-4o-mini",
        "anthropic_key": "",
        "anthropic_model": ANTHROPIC_BUDGET_MODELS[0],
    }


def _chat_path(cid: str) -> Path:
    return get_chats_dir() / f"{cid}.json"


def list_chat_meta() -> list[tuple[str, str, str]]:
    d = get_chats_dir()
    d.mkdir(parents=True, exist_ok=True)
    out: list[tuple[str, str, str]] = []
    for p in sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out.append((data.get("id", p.stem), data.get("title", p.stem), data.get("updated_utc", "")))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def _sidebar_chat_label(title: str, chat_id: str) -> str:
    """Avoid a column of identical 'New research' labels (legacy saves + defaults)."""
    t = (title or "").strip()
    if t in ("", "New research"):
        short = chat_id.replace("-", "")[:8] or chat_id[:8]
        return f"Draft · {short}"
    return t[:42] + ("…" if len(t) > 42 else "")


def _inject_layout_css() -> None:
    st.markdown(
        """
<style>
  .block-container {
    padding-top: 0.75rem !important;
    padding-bottom: 1rem !important;
  }
  header[data-testid="stHeader"] {
    background: transparent;
  }
  div[data-testid="stToolbar"] {
    top: 0.25rem;
  }
  .nm-brand-row {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    margin: 0 0 0.35rem 0;
    padding: 0;
  }
  .nm-brand-row img {
    width: 40px;
    height: 40px;
    flex-shrink: 0;
  }
  .nm-brand-title {
    font-size: 1.35rem;
    font-weight: 600;
    line-height: 1.2;
    margin: 0;
    letter-spacing: -0.02em;
  }
  .nm-brand-sub {
    font-size: 0.88rem;
    color: var(--secondary-text-color, #6b7280);
    margin: 0.1rem 0 0 0;
  }
  /* Compact main column */
  section.main div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] {
    margin-bottom: 0.35rem;
  }
  section.main .nm-composer-label {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--secondary-text-color, #6b7280);
    margin: 0.15rem 0 0.35rem 0;
  }
  /* Research composer textarea (main column) */
  section.main [data-testid="stTextArea"] textarea {
    border-radius: 22px !important;
    padding: 0.65rem 1rem !important;
    min-height: 2.75rem !important;
    line-height: 1.45 !important;
  }
  section.main [data-testid="stTextArea"] [data-baseweb="textarea"] {
    border-radius: 22px !important;
  }
  section.main div[data-testid="stPopover"] button {
    border-radius: 999px !important;
    min-height: 2.5rem;
    font-size: 1.15rem;
    font-weight: 500;
  }
</style>
        """,
        unsafe_allow_html=True,
    )


def _render_brand_header() -> None:
    if BRAND_MARK_SVG.is_file():
        b64 = base64.standard_b64encode(BRAND_MARK_SVG.read_bytes()).decode("ascii")
        src = f"data:image/svg+xml;base64,{b64}"
        st.markdown(
            f"""
<div class="nm-brand-row">
  <img src="{src}" width="40" height="40" alt="NovaMind" />
  <div>
    <p class="nm-brand-title">NovaMind</p>
    <p class="nm-brand-sub">Deep Research (chat)</p>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("### NovaMind · Deep Research (chat)")


def save_chat(data: dict) -> None:
    data["updated_utc"] = _utc_now()
    d = get_chats_dir()
    d.mkdir(parents=True, exist_ok=True)
    _chat_path(data["id"]).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_chat(cid: str) -> dict | None:
    path = _chat_path(cid)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def apply_chat_to_session(data: dict) -> None:
    for k, v in data.items():
        st.session_state[k] = v


def session_chat_dict() -> dict:
    cid = st.session_state.get("id") or str(uuid.uuid4())
    merged = _empty_chat(cid)
    for k in merged:
        if k in st.session_state:
            merged[k] = st.session_state[k]
    return merged


def ensure_session() -> None:
    get_chats_dir().mkdir(parents=True, exist_ok=True)
    if "id" not in st.session_state:
        cid = str(uuid.uuid4())
        apply_chat_to_session(_empty_chat(cid))
        save_chat(session_chat_dict())


def new_research_session() -> None:
    cid = str(uuid.uuid4())
    apply_chat_to_session(_empty_chat(cid))
    save_chat(session_chat_dict())


def persist_uploads(chat_id: str, files: list) -> list[str]:
    """Save Streamlit uploaded files to disk; return absolute paths."""
    if not files:
        return list(st.session_state.get("uploaded_paths") or [])
    up_dir = get_chats_dir() / chat_id / "uploads"
    up_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for uf in files:
        dest = up_dir / Path(uf.name).name
        dest.write_bytes(uf.getvalue())
        paths.append(str(dest.resolve()))
    return paths


def append_message(role: str, content: str) -> None:
    st.session_state.setdefault("messages", []).append({"role": role, "content": content})


def render_chat_messages() -> None:
    for m in st.session_state.get("messages") or []:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])


def main() -> None:
    st.set_page_config(page_title="NovaMind Research", layout="wide", initial_sidebar_state="expanded")
    _hydrate_google_env_from_streamlit_secrets()
    _ruri = os.environ.get("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8501/")
    if _ruri.startswith("http://") and ("localhost" in _ruri or "127.0.0.1" in _ruri):
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
    oauth_pair = _build_oauth_client_pair()
    if oauth_pair:
        client_cfg, redirect_uri = oauth_pair
        if _try_oauth_error_redirect():
            return
        if _try_oauth_callback(client_cfg, redirect_uri):
            return

    if not st.session_state.get("user_email"):
        if oauth_pair:
            _render_login_screen(oauth_pair[0], oauth_pair[1])
        else:
            _render_oauth_disabled_login_screen()
        st.stop()

    _inject_layout_css()
    ensure_session()

    _render_brand_header()

    col_side, col_main, col_right = st.columns([0.22, 0.48, 0.30], gap="medium")

    with col_side:
        st.caption(st.session_state.get("user_email", ""))
        if st.session_state.get("auth_anonymous"):
            st.caption("Anonymous test user (OAuth disabled)")
        if st.button("Sign out", use_container_width=True):
            logout_user()
            st.rerun()
        st.divider()
        st.caption("Chats")
        if st.button("➕ New research", use_container_width=True, type="primary"):
            new_research_session()
            st.rerun()

        for cid, title, _upd in list_chat_meta():
            label = _sidebar_chat_label(title, cid)
            if st.button(label, key=f"open_{cid}", use_container_width=True):
                data = load_chat(cid)
                if data:
                    merged = _empty_chat(data.get("id", cid))
                    merged.update(data)
                    tid = merged.get("id", cid)
                    if (merged.get("title") or "").strip() in ("", "New research"):
                        short = str(tid).replace("-", "")[:8] or str(tid)[:8]
                        merged["title"] = f"Draft · {short}"
                    apply_chat_to_session(merged)
                    save_chat(session_chat_dict())
                    st.rerun()

        st.divider()
        with st.expander("Model & API keys", expanded=False):
            _prov_opts = [LLM_PROVIDER_OPENROUTER, LLM_PROVIDER_ANTHROPIC]
            _prov_cur = st.session_state.get("llm_provider", LLM_PROVIDER_OPENROUTER)
            _prov_ix = _prov_opts.index(_prov_cur) if _prov_cur in _prov_opts else 0
            st.session_state["llm_provider"] = st.radio(
                "LLM backend",
                _prov_opts,
                index=_prov_ix,
                format_func=lambda x: "OpenRouter"
                if x == LLM_PROVIDER_OPENROUTER
                else "Anthropic (Haiku)",
            )
            if st.session_state["llm_provider"] == LLM_PROVIDER_OPENROUTER:
                st.session_state["openrouter_key"] = st.text_input(
                    "OpenRouter API key", type="password", value=st.session_state.get("openrouter_key", "")
                )
                _om = st.session_state.get("openrouter_model", "openai/gpt-4o-mini")
                _omi = (
                    OPENROUTER_MODEL_PRESETS.index(_om)
                    if _om in OPENROUTER_MODEL_PRESETS
                    else 0
                )
                st.session_state["openrouter_model"] = st.selectbox(
                    "Model",
                    OPENROUTER_MODEL_PRESETS,
                    index=_omi,
                )
            else:
                st.session_state["anthropic_key"] = st.text_input(
                    "Anthropic API key", type="password", value=st.session_state.get("anthropic_key", "")
                )
                _am = st.session_state.get("anthropic_model", ANTHROPIC_BUDGET_MODELS[0])
                _ami = (
                    ANTHROPIC_BUDGET_MODELS.index(_am)
                    if _am in ANTHROPIC_BUDGET_MODELS
                    else 0
                )
                st.session_state["anthropic_model"] = st.selectbox(
                    "Haiku model",
                    list(ANTHROPIC_BUDGET_MODELS),
                    index=_ami,
                )

        st.caption("Leave keys empty to use `.env` on the server.")

    with col_main:
        msgs = st.session_state.get("messages") or []
        _conv_open = bool(msgs)
        with st.expander("Conversation", expanded=_conv_open):
            if msgs:
                render_chat_messages()
            else:
                st.caption("Preview and research replies will show here.")

        st.markdown('<p class="nm-composer-label">Composer</p>', unsafe_allow_html=True)
        st.caption("Type below · **＋** uploads files (ChatGPT-style)")

        fu: list | tuple | None = None
        ac, ic = st.columns([1, 14], gap="small")
        with ac:
            with st.popover("＋", use_container_width=True):
                st.caption("Upload photos & files")
                fu = st.file_uploader(
                    "Attachments",
                    type=UPLOAD_FILE_TYPES,
                    accept_multiple_files=True,
                    label_visibility="collapsed",
                )
        with ic:
            st.session_state["question"] = st.text_area(
                "Research question",
                value=st.session_state.get("question", ""),
                height=90,
                placeholder="Ask anything…",
                label_visibility="collapsed",
            )

        paths = persist_uploads(st.session_state["id"], list(fu or []))
        if fu:
            st.session_state["uploaded_paths"] = paths
            save_chat(session_chat_dict())

        ups = st.session_state.get("uploaded_paths") or []
        if ups:
            chip = " · ".join(Path(p).name for p in ups)
            st.caption(f"**Attached:** {chip}")
            with st.expander("Uploaded file paths", expanded=False):
                for p in ups:
                    st.code(p, language=None)

        c_prev, c_run, c_cancel = st.columns([1, 1, 1], gap="small")
        preview_clicked = c_prev.button("Preview (human review)", use_container_width=True)
        run_clicked = c_run.button("Run full research", use_container_width=True, disabled=st.session_state.get("status") != "preview_ready")
        cancel_clicked = c_cancel.button("Cancel", use_container_width=True)

        with st.expander("Search & retrieval", expanded=False):
            st.session_state["enable_web_search"] = st.checkbox(
                "Tavily web search", value=st.session_state.get("enable_web_search", True)
            )
            s1, s2, s3 = st.columns(3)
            st.session_state["top_k"] = s1.slider(
                "Top-K (FAISS)", 2, 8, int(st.session_state.get("top_k", 4))
            )
            st.session_state["web_results_per_query"] = s2.slider(
                "Web hits / query", 1, 5, int(st.session_state.get("web_results_per_query", 3))
            )
            st.session_state["max_research_rounds"] = s3.slider(
                "Analyst passes", 1, 2, int(st.session_state.get("max_research_rounds", 1))
            )

        if cancel_clicked:
            append_message("assistant", "_Cancelled. Adjust your question or files and run **Preview** again._")
            st.session_state["status"] = "empty"
            save_chat(session_chat_dict())
            st.rerun()

        if preview_clicked:
            q = (st.session_state.get("question") or "").strip()
            if not q:
                st.error("Enter a research question first.")
            else:
                try:
                    settings = settings_from_ui(
                        st.session_state["llm_provider"],
                        st.session_state.get("openrouter_key", ""),
                        st.session_state.get("openrouter_model", ""),
                        st.session_state.get("anthropic_key", ""),
                        st.session_state.get("anthropic_model", ""),
                    )
                except ValueError as e:
                    st.error(str(e))
                    st.stop()
                append_message("user", f"**Question:** {q}\n\n_Preview requested._")
                with st.spinner("Running human preview (digest + alignment)…"):
                    try:
                        md, trace = run_preflight(q, st.session_state.get("uploaded_paths") or [], settings)
                    except Exception as e:
                        st.error(f"Preview failed: {e}")
                        st.stop()
                st.session_state["human_preview_md"] = md
                st.session_state["preflight_trace_md"] = trace
                st.session_state["status"] = "preview_ready"
                append_message("assistant", md)
                append_message("assistant", trace)
                st.session_state["title"] = derive_title("", q)
                save_chat(session_chat_dict())
                st.success("Preview ready — use **Run full research** or **Cancel**.")
                st.rerun()

        if run_clicked:
            q = (st.session_state.get("question") or "").strip()
            if not q:
                st.error("Enter a research question first.")
            else:
                try:
                    settings = settings_from_ui(
                        st.session_state["llm_provider"],
                        st.session_state.get("openrouter_key", ""),
                        st.session_state.get("openrouter_model", ""),
                        st.session_state.get("anthropic_key", ""),
                        st.session_state.get("anthropic_model", ""),
                    )
                except ValueError as e:
                    st.error(str(e))
                    st.stop()

                append_message("user", "**Run full research**")
                st.session_state["status"] = "running"
                save_chat(session_chat_dict())

                trace_box = st.empty()
                trace_box.markdown("_Starting research…_")

                def _cb(live: str) -> None:
                    trace_box.markdown(live)

                try:
                    last = run_research(
                        q,
                        st.session_state.get("uploaded_paths") or [],
                        settings,
                        enable_web_search=st.session_state["enable_web_search"],
                        top_k=st.session_state["top_k"],
                        web_results_per_query=st.session_state["web_results_per_query"],
                        max_research_rounds=st.session_state["max_research_rounds"],
                        progress_callback=_cb,
                    )
                except Exception as e:
                    st.session_state["status"] = "preview_ready"
                    save_chat(session_chat_dict())
                    st.error(f"Research failed: {e}")
                    st.stop()

                (
                    report_md,
                    gaps_md,
                    objective_md,
                    evidence_df,
                    trace_md,
                    contradictions_md,
                    full_md,
                    sources_detail,
                ) = finalize_research_outputs(last)

                title = derive_title(report_md, q)
                base = slug_filename_base(title)
                art_dir = get_chats_dir() / st.session_state["id"] / "artifacts"
                write_artifact_markdown(art_dir, base, full_md)

                st.session_state["report_md"] = report_md
                st.session_state["gaps_md"] = gaps_md
                st.session_state["objective_md"] = objective_md
                st.session_state["trace_md"] = trace_md
                st.session_state["contradictions_md"] = contradictions_md
                st.session_state["sources_detail_md"] = sources_detail
                st.session_state["evidence_records"] = evidence_df.to_dict(orient="records")
                st.session_state["artifact_base_name"] = base
                st.session_state["artifact_dir"] = str(art_dir)
                st.session_state["title"] = title
                st.session_state["status"] = "complete"
                append_message("assistant", f"**Research complete:** {title}\n\n_Open the tabs below and the report panel on the right._")
                save_chat(session_chat_dict())
                st.rerun()

        if st.session_state.get("status") == "complete":
            st.divider()
            t1, t2, t3, t4 = st.tabs(["Human review", "Report", "Sources", "Trace & gaps"])
            with t1:
                st.markdown(st.session_state.get("human_preview_md") or "_No preview stored._")
            with t2:
                st.markdown(st.session_state.get("report_md") or "_No report._")
                st.markdown("**Contradictions**")
                st.markdown(st.session_state.get("contradictions_md") or "_None noted._")
            with t3:
                recs = st.session_state.get("evidence_records") or []
                if recs:
                    st.dataframe(pd.DataFrame(recs), use_container_width=True, hide_index=True)
                st.markdown(st.session_state.get("sources_detail_md") or "")
            with t4:
                st.markdown(st.session_state.get("gaps_md") or "")
                st.markdown(st.session_state.get("trace_md") or "")

    with col_right:
        st.subheader("Report artifact")
        st.markdown(st.session_state.get("objective_md", ""))
        st.markdown(st.session_state.get("report_md") or "_Report appears here after a successful run._")

        base = st.session_state.get("artifact_base_name") or "research"
        full_md = ""
        art_dir = Path(st.session_state.get("artifact_dir") or get_chats_dir())
        md_path = art_dir / f"{base}.md" if base else None
        if md_path and md_path.is_file():
            full_md = md_path.read_text(encoding="utf-8")
        elif st.session_state.get("report_md"):
            detailed = st.session_state.get("sources_detail_md", "")
            full_md = st.session_state["report_md"]
            if detailed and detailed not in full_md:
                full_md = f"{full_md}\n\n---\n\n## Detailed extracts\n\n{detailed}"

        fn_base = slug_filename_base(st.session_state.get("title") or base or "research")

        st.download_button(
            label=f"Download {fn_base}.md",
            data=full_md.encode("utf-8") if full_md else b"",
            file_name=f"{fn_base}.md",
            mime="text/markdown",
            use_container_width=True,
            disabled=not full_md,
        )

        pdf_bytes = markdown_to_pdf_bytes(full_md) if full_md else None
        st.download_button(
            label=f"Download {fn_base}.pdf",
            data=pdf_bytes or b"",
            file_name=f"{fn_base}.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=pdf_bytes is None,
        )
        if full_md and pdf_bytes is None:
            st.caption("Install optional PDF deps: `pip install markdown xhtml2pdf`")


main()
