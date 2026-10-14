# yt_automation

yt_automation is a lightweight Python project for uploading local videos (especially Shorts) to YouTube using the YouTube Data API.

## Current status

This starter now supports:

- one-file uploads from the command line
- directory-based batch uploads
- OAuth credential handling for YouTube
- configurable defaults via environment variables
- repeatable uploads with simple metadata control

## Features

- Upload a single video file or all files in a folder
- Set title, description, tags, and privacy status
- Use environment or `.env` configuration defaults
- Minimal dependency footprint

## Project structure

```text
yt_automation/
├── app/
│   ├── __init__.py
│   ├── config.py
│   └── upload_short.py
├── credentials/
├── .gitignore
├── README.md
├── requirements.txt
├── config.example.env
└── .env.example
```

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create Google Cloud OAuth credentials:
   - Enable the YouTube Data API
   - Create OAuth client ID credentials
   - Download the JSON file as `client_secret.json`
   - Save it under `credentials/client_secret.json`

4. Copy the sample config and adjust it if needed:

```bash
cp config.example.env .env
```

5. Run an upload:

```bash
python -m app.upload_short --video /path/to/video.mp4 --title "My Short" --description "Uploaded using yt_automation" --tags "shorts,youtube,automation" --privacy private
```

Or upload all videos in a folder:

```bash
python -m app.upload_short --directory /path/to/videos --privacy private
```

## Example environment file

```bash
YOUTUBE_CLIENT_SECRET_PATH=credentials/client_secret.json
YOUTUBE_TOKEN_PATH=credentials/token.json
YOUTUBE_DEFAULT_PRIVACY=private
YOUTUBE_DEFAULT_TAGS=shorts,youtube,automation
```

## Remaining work

This is functional as a starter, but the project still needs finishing touches before production use:

- improve retry handling for API throttling and transient failures
- add a cleaner upload queue / multi-file progress display
- add comprehensive tests for validation and failure states
- implement scheduling or a cron-friendly workflow
- add better logging and operation summaries
- add a user-friendly config wizard
- prepare stricter validation for Shorts-specific metadata and file format checks

## Notes

- Vertical 9:16 videos work best for Shorts.
- Keep uploads within YouTube’s allowed file and API constraints.
- Be mindful of Google API quota usage.

## License

MIT
