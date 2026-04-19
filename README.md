# SocialBoost AI SaaS (Creator Repurposing MVP)

SocialBoost AI is a founder-friendly SaaS MVP that helps creators and marketers transform long-form or raw source content into short-form, monetizable content opportunities.

## What this MVP does

1. User creates an account and logs in.
2. User picks a paid package.
3. User submits source content as one of:
   - YouTube URL
   - uploaded video/audio/image file
   - pasted notes/transcript
4. App runs a **mock AI analysis pipeline** (replaceable later).
5. App returns structured short-form opportunities optimized for:
   - TikTok
   - YouTube Shorts

Each analysis returns:
- source summary
- main topic
- strongest hooks
- key moments and retention signals
- monetizable angles
- multiple short-form concepts (caption, CTA, framing, confidence)
- best recommended option + strategy rationale

## Stack

- Python + Flask
- SQLite
- Jinja templates + CSS
- Local upload storage (`uploads/`)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5000`

## Notes and limitations (MVP by design)

- Password storage is plain text (replace with hashing before production).
- Payment is simulated by choosing a package in the UI.
- Analysis is currently deterministic placeholder logic in `analyze_source_for_shorts` so you can validate UX quickly.
- Uploaded files are saved locally; no cloud object storage yet.

The placeholder analysis module is intentionally isolated so it can be swapped with real transcript/media + LLM analysis services later.
