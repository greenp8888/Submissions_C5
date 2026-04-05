"""Google OAuth helpers for Streamlit (authorization code flow)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from typing import Any

# OAuth ``state`` must survive a full browser redirect; Streamlit ``session_state`` may not.
_STATE_MAX_AGE_SEC = 600

import requests
from google_auth_oauthlib.flow import Flow

# Gmail consumer mailboxes only (includes legacy googlemail.com).
_GMAIL_DOMAINS = frozenset({"gmail.com", "googlemail.com"})

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def load_oauth_client_config(client_id: str, client_secret: str, redirect_uri: str) -> dict[str, Any]:
    if not client_id or not client_secret:
        raise ValueError("Google OAuth client id and secret are required.")
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


def create_flow(client_config: dict[str, Any], redirect_uri: str) -> Flow:
    # PKCE ties ``code_verifier`` to one ``Flow`` instance. We build a fresh Flow
    # for the token exchange after redirect, so auto-PKCE breaks with
    # ``invalid_grant: Missing code verifier``. Web clients with a client secret
    # do not require PKCE.
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        autogenerate_code_verifier=False,
    )


def create_signed_oauth_state(client_secret: str) -> str:
    """Return a self-contained ``state`` value verifiable with the same client secret (no server session)."""
    if not (client_secret or "").strip():
        raise ValueError("client_secret is required for signed OAuth state")
    secret = client_secret.strip()
    nonce = secrets.token_urlsafe(16)
    ts = str(int(time.time()))
    msg = f"{nonce}.{ts}"
    sig = hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    raw = f"{msg}.{sig}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def verify_signed_oauth_state(state: str, client_secret: str, max_age_sec: int = _STATE_MAX_AGE_SEC) -> bool:
    if not state or not (client_secret or "").strip():
        return False
    secret = client_secret.strip()
    try:
        pad = "=" * ((4 - len(state) % 4) % 4)
        decoded = base64.urlsafe_b64decode(state + pad).decode("utf-8")
        msg, sig = decoded.rsplit(".", 1)
        nonce, ts_str = msg.rsplit(".", 1)
        expected_sig = hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(expected_sig, sig):
            return False
        ts = int(ts_str)
        now = int(time.time())
        if now - ts > max_age_sec or ts > now + 120:
            return False
        del nonce  # used only for entropy in msg
        return True
    except Exception:
        return False


def authorization_url(flow: Flow, state: str) -> str:
    url, _ = flow.authorization_url(
        access_type="online",
        state=state,
        prompt="select_account",
    )
    return url


def exchange_code_and_fetch_email(
    client_config: dict[str, Any],
    redirect_uri: str,
    code: str,
) -> tuple[str, str]:
    """
    Exchange an auth code for tokens and return (email, display_name) from userinfo.
    """
    flow = create_flow(client_config, redirect_uri)
    flow.fetch_token(code=code)
    token = flow.credentials.token
    r = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    if not email:
        raise ValueError("Google did not return an email address.")
    return email, name


def is_allowed_gmail(email: str) -> bool:
    email = (email or "").strip().lower()
    if "@" not in email:
        return False
    domain = email.rsplit("@", 1)[-1]
    return domain in _GMAIL_DOMAINS


def sanitize_email_to_folder(email: str) -> str:
    """Map user@gmail.com -> user_gmail_com (only @ and . replaced per product spec)."""
    e = email.strip().lower()
    return e.replace("@", "_").replace(".", "_")


def read_oauth_settings_from_env() -> tuple[str, str, str]:
    """Returns (client_id, client_secret, redirect_uri)."""
    cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    sec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    redir = os.environ.get("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8501/").strip()
    return cid, sec, redir
