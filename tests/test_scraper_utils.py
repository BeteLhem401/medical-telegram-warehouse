"""
tests/test_scraper.py
=====================
Unit tests for scraper utility functions.
Tests the logic that doesn't require a live Telegram connection.

Run with:
    pytest tests/test_scraper_utils.py -v
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock

# We test the pure functions from scraper
# (no Telegram connection needed)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper import (
    get_data_lake_path,
    get_image_path,
    serialize_message,
    DATA_LAKE_ROOT,
    IMAGES_ROOT,
)


class TestGetDataLakePath:
    """Tests for the data lake file path builder."""

    def test_produces_correct_date_partition(self):
        date = datetime(2026, 6, 25)
        path = get_data_lake_path("lobelia4cosmetics", date)
        assert "2026-06-25" in str(path)

    def test_produces_correct_channel_filename(self):
        date = datetime(2026, 6, 25)
        path = get_data_lake_path("tikvahethiopia", date)
        assert path.name == "tikvahethiopia.json"

    def test_path_is_under_data_lake_root(self):
        date = datetime(2026, 6, 25)
        path = get_data_lake_path("test_channel", date)
        assert str(DATA_LAKE_ROOT) in str(path)


class TestGetImagePath:
    """Tests for the image storage path builder."""

    def test_produces_correct_channel_folder(self):
        path = get_image_path("lobelia4cosmetics", 12345)
        assert "lobelia4cosmetics" in str(path)

    def test_produces_correct_filename(self):
        path = get_image_path("lobelia4cosmetics", 12345)
        assert path.name == "12345.jpg"

    def test_path_is_under_images_root(self):
        path = get_image_path("test_channel", 99)
        assert str(IMAGES_ROOT) in str(path)


class TestSerializeMessage:
    """Tests for the message serialization function."""

    def _make_mock_message(self, **kwargs):
        """Create a mock Telethon message object."""
        msg = MagicMock()
        msg.id       = kwargs.get("id", 1001)
        msg.text     = kwargs.get("text", "Paracetamol 500mg available")
        msg.date     = kwargs.get("date", datetime(2026, 6, 25, tzinfo=timezone.utc))
        msg.media    = kwargs.get("media", None)
        msg.views    = kwargs.get("views", 150)
        msg.forwards = kwargs.get("forwards", 5)
        return msg

    def test_all_required_fields_present(self):
        msg = self._make_mock_message()
        result = serialize_message(msg, "test_channel", None)

        required_fields = [
            "message_id", "channel_name", "message_date",
            "message_text", "has_media", "image_path",
            "views", "forwards"
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_message_id_matches(self):
        msg = self._make_mock_message(id=9999)
        result = serialize_message(msg, "test_channel", None)
        assert result["message_id"] == 9999

    def test_channel_name_stored_correctly(self):
        msg = self._make_mock_message()
        result = serialize_message(msg, "lobelia4cosmetics", None)
        assert result["channel_name"] == "lobelia4cosmetics"

    def test_has_media_false_when_no_media(self):
        msg = self._make_mock_message(media=None)
        result = serialize_message(msg, "test_channel", None)
        assert result["has_media"] is False

    def test_has_media_true_when_media_present(self):
        msg = self._make_mock_message(media=MagicMock())
        result = serialize_message(msg, "test_channel", "/some/path.jpg")
        assert result["has_media"] is True

    def test_image_path_stored(self):
        msg = self._make_mock_message()
        result = serialize_message(msg, "test_channel", "/data/raw/images/ch/1.jpg")
        assert result["image_path"] == "/data/raw/images/ch/1.jpg"

    def test_empty_text_becomes_empty_string(self):
        msg = self._make_mock_message(text=None)
        result = serialize_message(msg, "test_channel", None)
        assert result["message_text"] == ""

    def test_views_defaults_to_zero(self):
        msg = self._make_mock_message(views=None)
        result = serialize_message(msg, "test_channel", None)
        assert result["views"] == 0

    def test_result_is_json_serializable(self):
        msg = self._make_mock_message()
        result = serialize_message(msg, "test_channel", None)
        # Should not raise
        json.dumps(result)
