"""Shared Google OAuth — one connection covers both Calendar (Section 14) and
Gmail (order intake) since both agent/google_calendar.py and
agent/gmail_client.py act on behalf of the same account with the same token.

Every function here fails soft — returns None/False on missing config,
missing auth, or any error — so the rest of the app behaves identically
whether or not Google has ever been connected.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

try:
    from google.auth.transport.requests import Request as GoogleAuthRequest
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    GoogleAuthRequest = None
    Credentials = None
    Flow = None
    build = None

# A second OAuth client (GOOGLE_CLIENT_ID_2/SECRET_2) was provisioned to add
# Gmail access — prefer it, falling back to the original Calendar-only client
# if it isn't set.
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID_2") or os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET_2") or os.getenv("GOOGLE_CLIENT_SECRET")
# Must exactly match an "Authorized redirect URI" on the OAuth client in Google
# Cloud Console. Defaults to the app root since that's what a Google OAuth
# client set up for this app would typically already have registered.
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI") or "http://127.0.0.1:8000/"
# oauthlib refuses to exchange a code over plain http, which would otherwise
# make exchange_code() fail silently for local (non-https) redirect URIs.
if REDIRECT_URI.startswith("http://"):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
]
TOKEN_PATH = Path(__file__).resolve().parents[1] / "token.json"


def _client_config():
    return {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }


def _configured() -> bool:
    return bool(Flow and CLIENT_ID and CLIENT_SECRET)


def _load_credentials():
    if not _configured() or not TOKEN_PATH.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    except (ValueError, OSError):
        return None
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleAuthRequest())
            TOKEN_PATH.write_text(creds.to_json())
        except Exception:
            # Most commonly: this token was issued by a different OAuth
            # client (e.g. before switching to GOOGLE_CLIENT_ID_2) and no
            # longer validates — treat as not connected until re-authorized.
            return None
    return creds if creds and creds.valid else None


def is_connected() -> bool:
    return _load_credentials() is not None


def get_auth_url():
    """Build the Google consent URL to redirect the user to. None if unconfigured."""
    if not _configured():
        return None
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    return auth_url


def exchange_code(code: str) -> bool:
    """Exchange an OAuth callback ``code`` for tokens and persist them to TOKEN_PATH."""
    if not _configured():
        return False
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES, redirect_uri=REDIRECT_URI)
    try:
        flow.fetch_token(code=code)
    except Exception as exc:
        import traceback
        (Path(__file__).resolve().parents[1] / "oauth_debug.log").write_text(
            f"{exc!r}\n\n{traceback.format_exc()}"
        )
        return False
    TOKEN_PATH.write_text(flow.credentials.to_json())
    return True


def get_service(api_name: str, api_version: str):
    """Build an authorized client for the given Google API, or None if not
    connected. Used by google_calendar.py ("calendar", "v3") and
    gmail_client.py ("gmail", "v1")."""
    creds = _load_credentials()
    if creds is None:
        return None
    return build(api_name, api_version, credentials=creds, cache_discovery=False)
