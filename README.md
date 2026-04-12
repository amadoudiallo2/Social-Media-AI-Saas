# SocialBoost AI SaaS (MVP)

A lightweight SaaS platform that lets clients:

1. Create an account.
2. Choose a paid package.
3. Generate social-media marketing content on demand (posts or promo video concepts).

## Features

- User sign-up and login.
- Paid package selection (Starter, Pro, Agency).
- Plan-aware generation limits:
  - Starter: 25 generations/month.
  - Pro / Agency: unlimited generations.
- Content generator form that accepts:
  - business name
  - target audience
  - campaign objective
  - tone
  - output type (post/video)
- Persistent history of recent generated outputs per user.

## Tech

- Python + Flask
- SQLite
- Jinja templates + simple CSS

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open: `http://127.0.0.1:5000`

> Note: This MVP uses plain password storage and simulated package payment logic. In production, add secure password hashing, a payment processor (e.g., Stripe), role-based access, rate limiting, and a real content/video generation backend.
