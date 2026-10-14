from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from googleapiclient.errors import HttpError

from app.config import load_settings, get_default_privacy, get_default_tags
from app.upload_short import build_upload_body, is_retryable_http_error, list_video_files, validate_video_file


class DummyResponse:
    status = 503


def test_load_settings_reads_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "YOUTUBE_CLIENT_SECRET_PATH=custom/client.json\n"
        "YOUTUBE_DEFAULT_PRIVACY=public\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("app.config.PROJECT_ROOT", tmp_path)
    settings = load_settings()

    assert settings["YOUTUBE_CLIENT_SECRET_PATH"] == "custom/client.json"
    assert settings["YOUTUBE_DEFAULT_PRIVACY"] == "public"
    assert settings["YOUTUBE_DEFAULT_TAGS"] == "shorts,youtube,automation"


def test_list_video_files_accepts_dir_and_single_file(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"123")

    assert list_video_files(str(video)) == [str(video)]

    folder = tmp_path / "videos"
    folder.mkdir()
    nested = folder / "nested.mov"
    nested.write_bytes(b"456")
    (folder / "notes.txt").write_text("not a video", encoding="utf-8")

    assert list_video_files(str(folder)) == [str(nested)]


def test_validate_video_file_rejects_empty_or_unsupported_files(tmp_path):
    bad_type = tmp_path / "clip.txt"
    bad_type.write_text("not a video", encoding="utf-8")

    with pytest.raises(ValueError):
        validate_video_file(str(bad_type))

    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")

    with pytest.raises(ValueError):
        validate_video_file(str(empty))


def test_build_upload_body_validates_metadata():
    body = build_upload_body("Hello world", "desc", ["tag1", "tag2"], "private")
    assert body["snippet"]["title"] == "Hello world"
    assert body["status"]["privacyStatus"] == "private"

    with pytest.raises(ValueError):
        build_upload_body("   ", "desc", ["tag"], "private")

    with pytest.raises(ValueError):
        build_upload_body("Title", "desc", ["tag"], "secret")


def test_is_retryable_http_error():
    exc = HttpError(DummyResponse(), b"{\"error\": {\"code\": 503}}")
    assert is_retryable_http_error(exc) is True

    exc2 = HttpError(DummyResponse(), b"{\"error\": {\"code\": 400}}")
    assert is_retryable_http_error(exc2) is False


def test_default_helpers_from_env(monkeypatch):
    monkeypatch.setenv("YOUTUBE_DEFAULT_PRIVACY", "public")
    monkeypatch.setenv("YOUTUBE_DEFAULT_TAGS", "shorts, youtube , automation")

    assert get_default_privacy() == "public"
    assert get_default_tags() == ["shorts", "youtube", "automation"]
