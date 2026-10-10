import os
import time
from pathlib import Path

import psycopg
from flask import Flask, jsonify, request, send_from_directory
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__)
INSTANCE_ID = os.getenv("INSTANCE_ID", "local")
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "notesdb"),
    "user": os.getenv("DB_USER", "appuser"),
    "password": os.getenv("DB_PASSWORD", "dev_password_123"),
    "connect_timeout": 3,
}


def connect_db():
    return psycopg.connect(**DB_CONFIG, row_factory=dict_row)


def init_db():
    """Create the table once the PostgreSQL service is ready."""
    last_error = None
    for attempt in range(1, 31):
        try:
            with connect_db() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notes (
                        id BIGSERIAL PRIMARY KEY,
                        text TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
            print("Database is ready; table 'notes' exists.", flush=True)
            return
        except psycopg.OperationalError as exc:
            last_error = exc
            print(f"Waiting for PostgreSQL ({attempt}/30)...", flush=True)
            time.sleep(2)
    raise RuntimeError(f"Could not connect to PostgreSQL: {last_error}")


def serialize_note(row):
    return {
        "id": row["id"],
        "text": row["text"],
        "created_at": row["created_at"].isoformat(),
    }


@app.get("/")
def home():
    # During Lab 0 Flask serves the page. In Lab 1, nginx serves this file itself.
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/api/health")
def health():
    try:
        with connect_db() as conn:
            conn.execute("SELECT 1")
        return jsonify({"status": "ok", "instance": INSTANCE_ID, "database": "connected"})
    except psycopg.Error:
        app.logger.exception("Database health check failed")
        return jsonify({"status": "error", "instance": INSTANCE_ID, "database": "unavailable"}), 503


@app.get("/api/notes")
def list_notes():
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT id, text, created_at FROM notes ORDER BY id DESC"
        ).fetchall()
    return jsonify({"instance": INSTANCE_ID, "notes": [serialize_note(row) for row in rows]})


@app.post("/api/notes")
def create_note():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Field 'text' must not be empty."}), 400

    with connect_db() as conn:
        row = conn.execute(
            "INSERT INTO notes (text) VALUES (%s) RETURNING id, text, created_at",
            (text.strip(),),
        ).fetchone()

    return jsonify({"instance": INSTANCE_ID, "note": serialize_note(row)}), 201


if __name__ == "__main__":
    init_db()
    # 0.0.0.0 is needed so the app is reachable from a Docker container/network.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
