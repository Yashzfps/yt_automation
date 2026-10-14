# yt_automation

A small Python utility to upload YouTube Shorts automatically from local video files.

## What this project does

- reads a local video file
- authenticates with the YouTube Data API
- uploads the file as a YouTube video
- supports basic metadata such as title, description, tags, and privacy status
- is designed to be extended for batch uploads and scheduled jobs

## Current status

This repo is intentionally scaffolded as a working starter, not a full production-ready uploader. The main pieces are in place, but some production work still remains.

## Quick start

1. Create a Google Cloud project and enable the YouTube Data API.
2. Create OAuth client credentials and download `client_secret.json`.
3. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Put your OAuth file in a folder like `credentials/client_secret.json`.
5. Run the uploader:

```bash
python app/upload_short.py \
  --video /path/to/short.mp4 \
  --title "My Short" \
  --description "Uploaded with yt_automation" \
  --tags "shorts,youtube,automation" \
  --privacy private
```

## Notes for Shorts

- Prefer a vertical 9:16 video.
- Keep videos short, ideally under 60 seconds.
- YouTube Shorts often work best with vertical framing and simple metadata.

## Remaining work

Before this becomes fully complete for real-world use, the following still needs to be done:

- add automated tests
- add better logging and retries
- handle OAuth refresh and credentials persistence cleanly
- support batch uploads from a folder
- add scheduling or cron support
- add config file support for defaults
- add a more robust CLI and error reporting
- validate upload behavior against YouTube API quotas and limits

## License

MIT
