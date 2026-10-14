# yt_automation

yt_automation is a lightweight Python project for uploading local videos (especially Shorts) to YouTube using the YouTube Data API.

## Current status

This project is now complete enough for practical use:

- single-file and directory-based uploads
- OAuth credential handling for YouTube
- configurable defaults via environment variables
- safer validation for local video files
- retry support for transient YouTube API errors
- clearer upload progress and queue reporting
- a simple configuration bootstrap command
- pytest coverage for key validation and config behavior

## Features

- Upload a single video file or all files in a folder
- Set title, description, tags, and privacy status
- Use environment or `.env` configuration defaults
- Validate video files before upload
- Retry transient API failures automatically
- Batch progress output and dry-run listing
- Minimal dependency footprint

## Project structure

```text
yt_automation/
├── app/
│   ├── __init__.py
│   ├── config.py
│   └── upload_short.py
├── tests/
│   └── test_upload_short.py
├── credentials/
├── .gitignore
├── README.md
├── requirements.txt
├── config.example.env
├── .env.example
└── .env
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

4. Create the default local config if needed:

```bash
python -m app.upload_short --init-config
```

This creates a `.env` file from the sample template and ensures the `credentials/` directory exists.

5. Run an upload:

```bash
python -m app.upload_short --video /path/to/video.mp4 --title "My Short" --description "Uploaded using yt_automation" --tags "shorts,youtube,automation" --privacy private
```

Or upload all videos in a folder:

```bash
python -m app.upload_short --directory /path/to/videos --privacy private
```

Check which files would be uploaded without sending them:

```bash
python -m app.upload_short --directory /path/to/videos --dry-run
```

## Example environment file

```bash
YOUTUBE_CLIENT_SECRET_PATH=credentials/client_secret.json
YOUTUBE_TOKEN_PATH=credentials/token.json
YOUTUBE_DEFAULT_PRIVACY=private
YOUTUBE_DEFAULT_TAGS=shorts,youtube,automation
```

## Notes

- Vertical 9:16 videos work best for Shorts.
- Keep uploads within YouTube’s allowed file and API constraints.
- Be mindful of Google API quota usage.
- The script retries transient API errors automatically, but quota or auth failures still need human intervention.

## License

MIT
