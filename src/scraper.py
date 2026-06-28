"""
src/scraper.py
==============
Telegram scraper for Ethiopian medical business channels.

What this script does:
  1. Connects to Telegram using your API credentials
  2. Scrapes messages from target medical/pharma channels
  3. Downloads images attached to messages
  4. Saves raw data as JSON into a partitioned data lake
  5. Logs all activity and errors

Data Lake Structure produced:
  data/raw/telegram_messages/YYYY-MM-DD/channel_name.json
  data/raw/images/channel_name/message_id.jpg
  logs/scraper_YYYY-MM-DD.log

Usage:
  python src/scraper.py
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

# Load credentials from .env file
load_dotenv()

API_ID   = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE    = os.getenv("TELEGRAM_PHONE", "")

# Target channels to scrape

TARGET_CHANNELS = [
    "lobelia4cosmetics",     # Lobelia Cosmetics
    "tikvahpharma",        # Tikvah Pharma
    "CheMed123",             # CheMed 
    
]

# How many messages to fetch per channel per run
# Start with 200 while testing; increase to 1000+ for production
MESSAGE_LIMIT = 200

# Root paths for the data lake
DATA_LAKE_ROOT = Path("data/raw/telegram_messages")
IMAGES_ROOT    = Path("data/raw/images")
LOGS_ROOT      = Path("logs")

# ─────────────────────────────────────────────────────────────
# LOGGING SETUP
# Logs go to both the terminal AND a file in logs/
# ─────────────────────────────────────────────────────────────

def setup_logging() -> logging.Logger:
    """Configure logging to write to both console and a dated log file."""
    LOGS_ROOT.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_ROOT / f"scraper_{today}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),  # write to file
            logging.StreamHandler(),                           # print to terminal
        ],
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_data_lake_path(channel_name: str, date: datetime) -> Path:
    """
    Build the partitioned data lake file path for a channel + date.

    Example:
        channel_name = "lobelia4cosmetics"
        date         = 2026-06-25
        → data/raw/telegram_messages/2026-06-25/lobelia4cosmetics.json
    """
    date_str = date.strftime("%Y-%m-%d")
    folder   = DATA_LAKE_ROOT / date_str
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{channel_name}.json"


def get_image_path(channel_name: str, message_id: int) -> Path:
    """
    Build the image storage path for a given channel + message.

    Example:
        → data/raw/images/lobelia4cosmetics/12345.jpg
    """
    folder = IMAGES_ROOT / channel_name
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{message_id}.jpg"


def serialize_message(message, channel_name: str, image_path: str | None) -> dict:
    """
    Convert a raw Telethon message object into a clean Python dictionary.
    This is the exact schema that gets stored in the JSON data lake.

    Fields match the project spec:
        message_id, channel_name, message_date, message_text,
        has_media, image_path, views, forwards
    """
    return {
        "message_id":   message.id,
        "channel_name": channel_name,
        "message_date": message.date.isoformat() if message.date else None,
        "message_text": message.text or "",        # empty string if no text
        "has_media":    message.media is not None,
        "image_path":   image_path,                # None if no image
        "views":        message.views or 0,
        "forwards":     message.forwards or 0,
        # Extra fields for debugging / future use
        "_scraped_at":  datetime.now(timezone.utc).isoformat(),
        "_raw_media_type": type(message.media).__name__ if message.media else None,
    }


# ─────────────────────────────────────────────────────────────
# CORE SCRAPING LOGIC
# ─────────────────────────────────────────────────────────────

async def scrape_channel(client: TelegramClient, channel_username: str) -> None:
    """
    Scrape all recent messages from a single Telegram channel.

    Process for each message:
      1. Extract text and metadata
      2. If it has a photo → download it
      3. Group messages by date → save to data lake as JSON
    """
    logger.info(f"Starting scrape: @{channel_username}")

    try:
        # Resolve the channel — this fetches channel metadata
        entity = await client.get_entity(channel_username)
        channel_display_name = entity.username or channel_username
        logger.info(f"Connected to channel: {entity.title} (@{channel_display_name})")

    except Exception as e:
        logger.error(f"Could not connect to @{channel_username}: {e}")
        return  # Skip this channel, continue with others

    # Group messages by date so we can partition the data lake
    # Structure: { "2026-06-25": [msg_dict, msg_dict, ...], ... }
    messages_by_date: dict[str, list[dict]] = {}

    scraped_count  = 0
    image_count    = 0
    skipped_count  = 0

    try:
        # iter_messages fetches messages in reverse-chronological order
        async for message in client.iter_messages(entity, limit=MESSAGE_LIMIT):

            # Skip messages with no content (e.g., service messages)
            if message.text is None and message.media is None:
                skipped_count += 1
                continue

            # ── Handle image download ──────────────────────────────
            image_path_str = None

            if isinstance(message.media, MessageMediaPhoto):
                img_path = get_image_path(channel_username, message.id)

                # Only download if we don't already have this image
                # (avoids re-downloading on repeat runs)
                if not img_path.exists():
                    try:
                        await client.download_media(message.media, file=str(img_path))
                        image_count += 1
                        logger.debug(f"Downloaded image: {img_path}")
                    except Exception as e:
                        logger.warning(f"Image download failed (msg {message.id}): {e}")
                else:
                    logger.debug(f"Image already exists, skipping: {img_path}")

                image_path_str = str(img_path)

            # ── Serialize the message ──────────────────────────────
            msg_dict = serialize_message(message, channel_username, image_path_str)

            # ── Group by date ──────────────────────────────────────
            if message.date:
                date_key = message.date.strftime("%Y-%m-%d")
            else:
                date_key = datetime.now().strftime("%Y-%m-%d")

            if date_key not in messages_by_date:
                messages_by_date[date_key] = []

            messages_by_date[date_key].append(msg_dict)
            scraped_count += 1

    except Exception as e:
        logger.error(f"Error while iterating messages in @{channel_username}: {e}")

    # ── Save to data lake ──────────────────────────────────────────
    # One JSON file per date per channel
    for date_str, messages in messages_by_date.items():
        date_dt   = datetime.strptime(date_str, "%Y-%m-%d")
        file_path = get_data_lake_path(channel_username, date_dt)

        # If file already exists (from a previous run), merge intelligently
        existing_messages = []
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_messages = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not read existing file {file_path}, overwriting.")

        # Merge: keep existing, add new ones (avoid duplicates by message_id)
        existing_ids = {m["message_id"] for m in existing_messages}
        new_messages = [m for m in messages if m["message_id"] not in existing_ids]
        all_messages = existing_messages + new_messages

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(all_messages, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Saved {len(new_messages)} new messages "
            f"(+{len(existing_messages)} existing) → {file_path}"
        )

    logger.info(
        f"Finished @{channel_username}: "
        f"{scraped_count} messages scraped, "
        f"{image_count} images downloaded, "
        f"{skipped_count} messages skipped"
    )


# ─────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

async def main():
    """
    Main coroutine: initializes the Telegram client and scrapes all channels.
    """
    # Validate credentials are loaded
    if not API_ID or not API_HASH:
        logger.error(
            "Missing Telegram API credentials!\n"
            "  1. Copy .env.example to .env\n"
            "  2. Fill in TELEGRAM_API_ID and TELEGRAM_API_HASH\n"
            "  Get credentials at: https://my.telegram.org"
        )
        return

    logger.info("=" * 60)
    logger.info("Kara Solutions — Medical Telegram Scraper")
    logger.info(f"Channels to scrape: {TARGET_CHANNELS}")
    logger.info(f"Message limit per channel: {MESSAGE_LIMIT}")
    logger.info("=" * 60)

    # The session file saves your Telegram login so you don't
    # need to re-authenticate every run. It's gitignored.
    async with TelegramClient("telegram_session", API_ID, API_HASH) as client:
        logger.info("Telegram client connected.")

        for channel in TARGET_CHANNELS:
            await scrape_channel(client, channel)
            # Small delay between channels to avoid rate limiting
            await asyncio.sleep(2)

    logger.info("=" * 60)
    logger.info("Scraping complete. Check data/raw/ for your data lake.")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
