"""
Shared database connection helper.
Reads the Postgres/Supabase connection string from Streamlit secrets
(when deployed) or from the .env file (when running locally), and
exposes a single get_connection() function used by auth.py and progress.py.
"""

import os
import re
import psycopg2
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    _HAS_STREAMLIT_SECRETS = True
except Exception:
    _HAS_STREAMLIT_SECRETS = False


def _fix_password_encoding(db_url: str) -> str:
    """
    Connection strings break if the password contains reserved URL characters
    (like @, :, /, etc.) since they collide with the URL's own separators.
    This safely re-encodes just the password portion, regardless of what
    special characters it contains, without touching the rest of the URL.
    """
    match = re.match(r"^(postgresql(?:\+\w+)?://[^:]+:)(.+)(@[^@]+)$", db_url)
    if not match:
        return db_url

    prefix, raw_password, suffix = match.groups()
    encoded_password = quote(raw_password, safe="")
    return f"{prefix}{encoded_password}{suffix}"


def _get_db_url() -> str:
    if _HAS_STREAMLIT_SECRETS:
        try:
            raw = st.secrets["SUPABASE_DB_URL"]
            return _fix_password_encoding(raw)
        except Exception:
            pass
    raw = os.getenv("SUPABASE_DB_URL")
    return _fix_password_encoding(raw) if raw else raw


def get_connection():
    db_url = _get_db_url()
    if not db_url:
        raise RuntimeError(
            "SUPABASE_DB_URL is not set. Add it to .env (local) or "
            "Streamlit secrets (deployed)."
        )
    return psycopg2.connect(db_url)