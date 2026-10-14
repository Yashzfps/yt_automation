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

# Scope needed to upload videos to YouTube.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_credentials(token_path: str, client_secret_path: str) -> Credentials:
    """Reads an existing token or opens OAuth flow to generate one."""
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


def upload_short(video_path: str, title: str, description: str, tags: list[str], privacy: str):
    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    token_path = os.environ.get("YOUTUBE_TOKEN_PATH", "credentials/token.json")
    client_secret_path = os.environ.get("YOUTUBE_CLIENT_SECRET_PATH", "credentials/client_secret.json")

    if not os.path.exists(client_secret_path):
        raise FileNotFoundError(
            "Missing OAuth client_secret.json. Create credentials/client_secret.json from Google Cloud."
        )

    os.makedirs(os.path.dirname(token_path) or ".", exist_ok=True)
    creds = get_credentials(token_path, client_secret_path)

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

    print("Upload complete")
    print(f"Video ID: {response['id']}")
    return response


def parse_args():
    parser = argparse.ArgumentParser(description="Upload a local video to YouTube as a short.")
    parser.add_argument("--video", required=True, help="Path to the local video file.")
    parser.add_argument("--title", required=True, help="YouTube video title.")
    parser.add_argument("--description", default="Uploaded with yt_automation.")
    parser.add_argument("--tags", default="shorts,youtube,automation", help="Comma-separated tags.")
    parser.add_argument("--privacy", default="private", choices=["private", "public", "unlisted"])
    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = parse_args()
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        upload_short(args.video, args.title, args.description, tags, args.privacy)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except HttpError as exc:
        print(f"YouTube API error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)
