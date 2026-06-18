"""
Handles user signup and login against the `users` table in Supabase.
Passwords are hashed with bcrypt before storage — the plain password
is never saved anywhere.
"""

import bcrypt
from modules.db import get_connection


def signup(username: str, password: str) -> tuple[bool, str]:
    username = username.strip()

    if not username or not password:
        return False, "Username and password cannot be empty."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, "That username is already taken."

        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, "Account created! You can now log in."
    except Exception as e:
        return False, f"Signup failed: {e}"


def login(username: str, password: str) -> tuple[bool, str]:
    username = username.strip()

    if not username or not password:
        return False, "Please enter both username and password."

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return False, "No account found with that username."

        stored_hash = row[0].encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return True, "Login successful."
        else:
            return False, "Incorrect password."
    except Exception as e:
        return False, f"Login failed: {e}"