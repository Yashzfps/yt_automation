from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from app.config import DEFAULT_ENV_TEMPLATE, PROJECT_ROOT, get_client_secret_path, get_default_privacy, get_default_tags, get_token_path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SUPPORTED_VIDEO_TYPES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
LOGGER = logging.getLogger("yt_automation")


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s: %(message)s",
    )


def ensure_parent_dir(path: str) -> None:
    parent = Path(path).parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def init_config_file() -> Path:
    env_file = PROJECT_ROOT / ".env"
    credentials_dir = PROJECT_ROOT / "credentials"
    credentials_dir.mkdir(exist_ok=True)

    if not env_file.exists():
        env_file.write_text(DEFAULT_ENV_TEMPLATE, encoding="utf-8")
        print(f"Created default config at {env_file}")
    else:
        print(f"Config already exists at {env_file}")

    return env_file


def validate_video_file(video_path: str) -> None:
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not path.is_file():
        raise ValueError(f"Video path is not a file: {video_path}")
    if path.suffix.lower() not in SUPPORTED_VIDEO_TYPES:
        raise ValueError(
            f"Unsupported video type for {video_path}. Supported formats: {sorted(SUPPORTED_VIDEO_TYPES)}"
        )
    if path.stat().st_size == 0:
        raise ValueError(f"Video file is empty: {video_path}")


def is_retryable_http_error(exc: HttpError) -> bool:
    status = getattr(exc, "resp", None)
    code = getattr(status, "status", None)
    if code in {429, 500, 502, 503, 504}:
        return True

    raw_content = getattr(exc, "content", b"") or b""
    if isinstance(raw_content, bytes):
        text = raw_content.decode("utf-8", "ignore").lower()
    else:
        text = str(raw_content).lower()

    tokens = [
        "rate limit",
        "quota",
        "backenderror",
        "internalerror",
        "temporarily unavailable",
        "throttled",
        "transient",
    ]
    return any(token in text for token in tokens)


def get_credentials() -> Credentials:
    client_secret_path = get_client_secret_path()
    token_path = get_token_path()

    if not os.path.exists(client_secret_path):
        raise FileNotFoundError(
            f"Missing OAuth client_secret.json at {client_secret_path}. "
            "Create it from Google Cloud and try again."
        )

    ensure_parent_dir(token_path)
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return creds


def build_upload_body(title: str, description: str, tags: list[str], privacy: str) -> dict:
    cleaned_title = (title or "").strip()
    if not cleaned_title:
        raise ValueError("Video title cannot be empty")
    if privacy not in {"private", "public", "unlisted"}:
        raise ValueError(f"Unsupported privacy setting: {privacy}")

    return {
        "snippet": {
            "title": cleaned_title,
            "description": description,
            "tags": [tag.strip() for tag in tags if tag and tag.strip()],
            "categoryId": "24",
        },
        "status": {"privacyStatus": privacy},
    }


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy: str,
    max_retries: int = 3,
) -> dict:
    validate_video_file(video_path)

    last_error: HttpError | None = None
    for attempt in range(max_retries + 1):
        try:
            creds = get_credentials()
            youtube = build("youtube", "v3", credentials=creds)
            body = build_upload_body(title, description, tags, privacy)
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

            request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    LOGGER.info("Upload progress: %s bytes uploaded", status.resumable_progress)

            return response
        except HttpError as exc:
            last_error = exc
            if not is_retryable_http_error(exc) or attempt >= max_retries:
                raise
            delay = 2 ** attempt
            LOGGER.warning(
                "Upload failed for %s (attempt %s/%s). Retrying in %ss.",
                video_path,
                attempt + 1,
                max_retries + 1,
                delay,
            )
            time.sleep(delay)

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Upload failed for {video_path}")


def list_video_files(source: str, recursive: bool = False) -> list[str]:
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {source}")

    if path.is_file():
        validate_video_file(str(path))
        return [str(path)]

    if recursive:
        files = [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_VIDEO_TYPES]
    else:
        files = [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_VIDEO_TYPES]

    return [str(file_path) for file_path in sorted(files)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload one or more local videos to YouTube as Shorts.")
    parser.add_argument("--video", help="Single video file to upload.")
    parser.add_argument("--directory", help="Folder containing videos to upload.")
    parser.add_argument("--title", help="Title to use for the upload. Defaults to the file name.")
    parser.add_argument("--description", default="Uploaded with yt_automation.")
    parser.add_argument("--tags", default=",".join(get_default_tags()))
    parser.add_argument("--privacy", default=get_default_privacy(), choices=["private", "public", "unlisted"])
    parser.add_argument("--recursive", action="store_true", help="Include nested files when uploading from a directory.")
    parser.add_argument("--dry-run", action="store_true", help="List files that would be uploaded without uploading them.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    parser.add_argument("--max-retries", type=int, default=3, help="Retry transient YouTube API errors up to this many times.")
    parser.add_argument("--init-config", action="store_true", help="Create a default .env file and credentials directory if they do not exist.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)

    if args.init_config:
        init_config_file()
        return

    if bool(args.video) == bool(args.directory):
        print("Provide either --video or --directory, but not both.", file=sys.stderr)
        sys.exit(1)

    source = args.video or args.directory
    try:
        video_files = list_video_files(source, recursive=args.recursive)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if not video_files:
        print(f"No supported video files found in {source}.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        for file_path in video_files:
            print(file_path)
        return

    total = len(video_files)
    for index, file_path in enumerate(video_files, start=1):
        file_name = Path(file_path).stem
        title = args.title or file_name
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        print(f"[{index}/{total}] Uploading: {file_path}")
        try:
            result = upload_video(file_path, title, args.description, tags, args.privacy, max_retries=args.max_retries)
            print(f"[{index}/{total}] Upload complete for {file_path}. Video ID: {result.get('id')}")
        except HttpError as exc:
            print(f"[{index}/{total}] Upload failed for {file_path}: {exc}", file=sys.stderr)
        except ValueError as exc:
            print(f"[{index}/{total}] Invalid video or metadata for {file_path}: {exc}", file=sys.stderr)
        except Exception as exc:
            print(f"[{index}/{total}] Unexpected error for {file_path}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
