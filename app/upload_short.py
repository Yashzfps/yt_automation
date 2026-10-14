from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from app.config import get_client_secret_path, get_default_privacy, get_default_tags, get_token_path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def ensure_parent_dir(path: str) -> None:
    parent = Path(path).parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


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
    return {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "24",
        },
        "status": {"privacyStatus": privacy},
    }


def upload_video(video_path: str, title: str, description: str, tags: list[str], privacy: str) -> dict:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

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
            print(f"Upload progress: {status.resumable_progress} bytes uploaded")

    return response


def list_video_files(source: str, recursive: bool = False) -> list[str]:
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {source}")

    if path.is_file():
        return [str(path)]

    suffixes = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    if recursive:
        files = [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in suffixes]
    else:
        files = [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in suffixes]
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if bool(args.video) == bool(args.directory):
        print("Provide either --video or --directory, but not both.", file=sys.stderr)
        sys.exit(1)

    source = args.video or args.directory
    video_files = list_video_files(source, recursive=args.recursive)

    if args.dry_run:
        for file_path in video_files:
            print(file_path)
        return

    for file_path in video_files:
        file_name = Path(file_path).stem
        title = args.title or file_name
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        print(f"Uploading: {file_path}")
        try:
            result = upload_video(file_path, title, args.description, tags, args.privacy)
            print(f"Upload complete for {file_path}. Video ID: {result.get('id')}")
        except HttpError as exc:
            print(f"Upload failed for {file_path}: {exc}", file=sys.stderr)
        except Exception as exc:
            print(f"Unexpected error for {file_path}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
