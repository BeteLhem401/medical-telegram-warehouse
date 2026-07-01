"""
Task 2 — Load raw Telegram JSON data into PostgreSQL
Reads all JSON files from data/raw/telegram_messages/
and inserts them into the raw_messages table.
"""

import json
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# ── Database connection ───────────────────────────────────────────
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "medical_warehouse")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ── Create table if it does not exist ────────────────────────────
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_messages (
    id               SERIAL PRIMARY KEY,
    message_id       BIGINT,
    channel_name     TEXT,
    message_date     TIMESTAMPTZ,
    message_text     TEXT,
    has_media        BOOLEAN,
    image_path       TEXT,
    views            INTEGER,
    forwards         INTEGER,
    scraped_at       TIMESTAMPTZ,
    loaded_at        TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_message UNIQUE (message_id, channel_name)
);
"""

# ── Load all JSON files ───────────────────────────────────────────
def load_all_json_files():
    data_path = Path("data/raw/telegram_messages")
    records = []

    for date_folder in sorted(data_path.iterdir()):
        if not date_folder.is_dir():
            continue
        for json_file in date_folder.glob("*.json"):
            with open(json_file, encoding="utf-8") as f:
                messages = json.load(f)
                records.extend(messages)

    return records


# ── Insert records into PostgreSQL ───────────────────────────────
def insert_records(engine, records):
    insert_sql = text("""
        INSERT INTO raw_messages (
            message_id, channel_name, message_date, message_text,
            has_media, image_path, views, forwards, scraped_at
        )
        VALUES (
            :message_id, :channel_name, :message_date, :message_text,
            :has_media, :image_path, :views, :forwards, :scraped_at
        )
        ON CONFLICT DO NOTHING
    """)

    with engine.begin() as conn:
        for record in records:
            conn.execute(insert_sql, {
                "message_id":   record.get("message_id"),
                "channel_name": record.get("channel_name"),
                "message_date": record.get("message_date"),
                "message_text": record.get("message_text"),
                "has_media":    record.get("has_media"),
                "image_path":   record.get("image_path"),
                "views":        record.get("views"),
                "forwards":     record.get("forwards"),
                "scraped_at":   record.get("_scraped_at"),
            })


# ── Main ─────────────────────────────────────────────────────────
def main():
    print("Connecting to PostgreSQL...")
    engine = create_engine(DATABASE_URL)

    print("Creating table if not exists...")
    with engine.begin() as conn:
        conn.execute(text(CREATE_TABLE_SQL))

    print("Loading JSON files...")
    records = load_all_json_files()
    print(f"Found {len(records)} messages to load")

    print("Inserting into database...")
    insert_records(engine, records)
    print("Done.")


if __name__ == "__main__":
    main()