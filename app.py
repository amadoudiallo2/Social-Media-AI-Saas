from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "saas.db"
UPLOAD_DIR = BASE_DIR / "uploads"
ALLOWED_UPLOAD_EXTENSIONS = {"mp4", "mov", "m4v", "mp3", "wav", "m4a", "png", "jpg", "jpeg", "webp"}

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "saas.db"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret")

PACKAGES = {
    "starter": {
        "name": "Starter",
        "price": 29,
        "description": "Best for solo creators validating short-form ideas.",
        "description": "Good for solopreneurs creating posts and captions.",
        "limit": 25,
    },
    "pro": {
        "name": "Pro",
        "price": 99,
        "description": "Unlimited short-form curation for creators and marketers.",
        "description": "Unlimited text + image ideas and short-form video concepts.",
        "limit": -1,
    },
    "agency": {
        "name": "Agency",
        "price": 249,
        "description": "Unlimited analyses for teams repurposing at scale.",
        "description": "Unlimited generations + team support and priority queue.",
        "limit": -1,
    },
}


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def teardown_db(exception: BaseException | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def add_column_if_missing(db: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_db() -> None:
    UPLOAD_DIR.mkdir(exist_ok=True)

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            package_id TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            business_name TEXT NOT NULL,
            audience TEXT NOT NULL,
            objective TEXT NOT NULL,
            tone TEXT NOT NULL,
            output TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )

    # Lightweight schema migration for older local DBs.
    add_column_if_missing(db, "generations", "source_type", "TEXT")
    add_column_if_missing(db, "generations", "source_reference", "TEXT")
    add_column_if_missing(db, "generations", "uploaded_file", "TEXT")

    db.commit()
    db.close()


def current_user() -> sqlite3.Row | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def can_generate(user: sqlite3.Row) -> bool:
    package_id = user["package_id"]
    if not package_id:
        return False
    package = PACKAGES.get(package_id)
    if not package:
        return False
    if package["limit"] == -1:
        return True
    db = get_db()
    count = db.execute(
        "SELECT COUNT(*) AS total FROM generations WHERE user_id = ?", (user["id"],)
    ).fetchone()["total"]
    return count < package["limit"]


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def parse_youtube_id(url: str) -> str | None:
    parsed = urlparse(url)
    if "youtube.com" in parsed.netloc and "v=" in parsed.query:
        for part in parsed.query.split("&"):
            if part.startswith("v="):
                return part.split("=", 1)[1]
    if "youtu.be" in parsed.netloc:
        return parsed.path.strip("/")
    return None


def ingest_source_from_request() -> dict[str, str]:
    youtube_url = request.form.get("youtube_url", "").strip()
    source_notes = request.form.get("source_notes", "").strip()
    uploaded = request.files.get("source_file")

    if youtube_url:
        youtube_id = parse_youtube_id(youtube_url)
        return {
            "source_type": "youtube_url",
            "source_reference": youtube_url,
            "uploaded_file": "",
            "source_summary": (
                f"YouTube source detected ({'video id: ' + youtube_id if youtube_id else 'valid link provided'})."
            ),
        }

    if uploaded and uploaded.filename:
        ext = get_file_extension(uploaded.filename)
        if ext not in ALLOWED_UPLOAD_EXTENSIONS:
            raise ValueError("Unsupported upload type. Use video, audio, or image files.")

        safe_name = secure_filename(uploaded.filename)
        stored_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{safe_name}"
        saved_path = UPLOAD_DIR / stored_name
        uploaded.save(saved_path)
        upload_kind = "image/screenshot" if ext in {"png", "jpg", "jpeg", "webp"} else "video/audio"
        return {
            "source_type": "file_upload",
            "source_reference": source_notes or f"Uploaded {upload_kind} source",
            "uploaded_file": str(saved_path.relative_to(BASE_DIR)),
            "source_summary": f"{upload_kind.title()} uploaded: {safe_name}",
        }

    if source_notes:
        return {
            "source_type": "raw_notes",
            "source_reference": source_notes,
            "uploaded_file": "",
            "source_summary": "Raw creator notes/transcript provided.",
        }

    raise ValueError("Provide a YouTube URL, upload a media file, or add raw notes/transcript.")


def analyze_source_for_shorts(payload: dict[str, Any]) -> dict[str, Any]:
    """MVP placeholder analysis layer; swap with real media/LLM analysis service later."""
def generate_marketing_content(payload: dict[str, Any]) -> str:
    business = payload["business_name"]
    audience = payload["audience"]
    objective = payload["objective"]
    tone = payload["tone"]
    source_summary = payload["source_summary"]

    hooks = [
        f"Stop scrolling: {audience} are making this {objective} mistake.",
        f"How {business} turns one idea into multiple short-form wins.",
        f"The 20-second framework behind faster creator monetization.",
    ]

    key_moments = [
        "Tension point appears in the first 3-5 seconds with a direct problem statement.",
        "Middle segment introduces a clear transformation or outcome proof.",
        "Ending segment creates urgency with one measurable CTA.",
    ]

    emotional_segments = [
        "Relief: viewers feel a path from confusion to clarity.",
        "Ambition: creator/brand growth angle with concrete upside.",
        "FOMO: highlights what audience misses by delaying action.",
    ]

    options = [
        {
            "title_hook": hooks[0],
            "platform": "TikTok",
            "angle_summary": "Problem-first hook + quick 3-step fix from source content.",
            "why_it_may_perform": "Strong interruption hook and concise payoff increase retention.",
            "caption": "Most creators waste content by posting once. Repurpose smarter. #contentstrategy #tiktokgrowth",
            "cta": "Comment 'PLAN' for the repurposing checklist.",
            "clip_framing": "Vertical 9:16, fast jump cuts, bold captions, pattern interrupt at second 2.",
            "confidence": "High",
            "virality_rationale": "Problem/solution framing is highly remixable and shareable.",
        },
        {
            "title_hook": hooks[1],
            "platform": "YouTube Shorts",
            "angle_summary": "Behind-the-scenes breakdown of how one long-form input became multiple clips.",
            "why_it_may_perform": "Educational + tactical format performs well with creator audiences.",
            "caption": "Turn one video into a full week of shorts. Here's the exact structure.",
            "cta": "Subscribe for weekly repurposing playbooks.",
            "clip_framing": "Screen recording + talking head, chapter-style on-screen text.",
            "confidence": "Medium-High",
            "virality_rationale": "Clear framework content drives saves and rewatches.",
        },
        {
            "title_hook": hooks[2],
            "platform": "TikTok",
            "angle_summary": "Monetization-focused clip: map one insight to offer, CTA, and conversion path.",
            "why_it_may_perform": "Outcome-driven content attracts business-minded viewers with buying intent.",
            "caption": "Views are nice. Revenue is better. Use this 20-second monetization angle.",
            "cta": "DM 'SHORTS' to get a done-for-you script template.",
            "clip_framing": "Talking head + proof screenshot overlay + single CTA end card.",
            "confidence": "High",
            "virality_rationale": "Monetization promise creates high curiosity and comment intent.",
        },
    ]

    return {
        "source_content_summary": source_summary,
        "main_topic": f"{business} content repurposing for {audience}",
        "strongest_hooks": hooks,
        "key_moments": key_moments,
        "emotional_or_retention_segments": emotional_segments,
        "clipworthy_sections": [
            "0-8s: sharp hook + pain statement",
            "8-22s: concise value demonstration",
            "22-35s: monetization angle + concrete CTA",
        ],
        "monetizable_angles": [
            f"Lead with {objective} and route viewers to an offer-focused CTA.",
            "Offer a checklist/template download to capture leads.",
            "Use comment keyword CTA to trigger DM funnel follow-up.",
        ],
        "audience_relevance": f"Tailored to {audience} with a {tone} delivery style.",
        "platform_fit": "Optimized primarily for TikTok and YouTube Shorts (9:16, hook in first 2 seconds).",
        "short_form_options": options,
        "best_recommended_option": options[0],
        "strategy_rationale": (
            "Best option balances instant hook clarity, retention pacing, and direct monetization CTA, "
            "which is strongest for short-form performance and conversion intent."
        ),
        "mock_note": "MVP placeholder analysis: replace with real transcript/media intelligence service later.",
    }
    content_type = payload["content_type"]

    if content_type == "video":
        return (
            f"30-second promo video plan for {business}:\\n"
            f"1) Hook (0-5s): A bold statement for {audience} in a {tone} tone.\\n"
            f"2) Problem (5-10s): Show the main pain point related to {objective}.\\n"
            f"3) Solution (10-20s): Demonstrate how {business} solves it with clear visuals.\\n"
            f"4) Social Proof (20-26s): Add one customer quote and before/after insight.\\n"
            f"5) CTA (26-30s): 'Message us today to get started.'\\n"
            "Visual style: Fast cuts, subtitles, brand colors, and upbeat background audio."
        )

    return (
        f"Campaign post for {business}:\\n"
        f"Audience: {audience}\\n"
        f"Objective: {objective}\\n"
        f"Tone: {tone}\\n"
        "Caption: Ready to transform your results? Let's make your next win simple, measurable, and repeatable.\\n"
        "CTA: Click the link in bio or send us a DM to get a personalized offer today."
    )


@app.route("/")
def index() -> str:
    return render_template("index.html", packages=PACKAGES)


@app.route("/signup", methods=["GET", "POST"])
def signup() -> str:
    if request.method == "POST":
        db = get_db()
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()
        if not full_name or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("signup"))

        try:
            db.execute(
                "INSERT INTO users (full_name, email, password, created_at) VALUES (?, ?, ?, ?)",
                (full_name, email, password, datetime.utcnow().isoformat()),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("Email already exists.")
            return redirect(url_for("signup"))

        flash("Account created. Please log in.")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login() -> str:
    if request.method == "POST":
        db = get_db()
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()
        user = db.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?", (email, password)
        ).fetchone()

        if not user:
            flash("Invalid credentials.")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        flash("Welcome back!")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout() -> str:
    session.clear()
    flash("You are logged out.")
    return redirect(url_for("index"))


@app.route("/subscribe/<package_id>", methods=["POST"])
def subscribe(package_id: str) -> str:
    user = current_user()
    if not user:
        flash("Please log in before selecting a package.")
        return redirect(url_for("login"))

    if package_id not in PACKAGES:
        flash("Package not found.")
        return redirect(url_for("dashboard"))

    db = get_db()
    db.execute("UPDATE users SET package_id = ? WHERE id = ?", (package_id, user["id"]))
    db.commit()
    flash(f"Subscribed to {PACKAGES[package_id]['name']} plan.")
    return redirect(url_for("dashboard"))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard() -> str:
    user = current_user()
    if not user:
        flash("Please log in first.")
        return redirect(url_for("login"))

    db = get_db()

    if request.method == "POST":
        if not can_generate(user):
            flash("Analysis limit reached or no plan selected.")
            return redirect(url_for("dashboard"))

        try:
            source_payload = ingest_source_from_request()
        except ValueError as exc:
            flash(str(exc))
            return redirect(url_for("dashboard"))

        payload = {
            "content_type": "short_form_repurpose",
            "business_name": request.form["business_name"].strip(),
            "audience": request.form["audience"].strip(),
            "objective": request.form["objective"].strip(),
            "tone": request.form["tone"].strip() or "clear",
            "source_summary": source_payload["source_summary"],
        }

        report = analyze_source_for_shorts(payload)
        db.execute(
            """
            INSERT INTO generations
            (user_id, content_type, business_name, audience, objective, tone, output, created_at, source_type, source_reference, uploaded_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    generated = db.execute(
        "SELECT * FROM generations WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user["id"],)
    ).fetchall()

    if request.method == "POST":
        if not can_generate(user):
            flash("Generation limit reached or no plan selected.")
            return redirect(url_for("dashboard"))

        payload = {
            "content_type": request.form["content_type"],
            "business_name": request.form["business_name"],
            "audience": request.form["audience"],
            "objective": request.form["objective"],
            "tone": request.form["tone"],
        }
        output = generate_marketing_content(payload)
        db.execute(
            """
            INSERT INTO generations
            (user_id, content_type, business_name, audience, objective, tone, output, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                payload["content_type"],
                payload["business_name"],
                payload["audience"],
                payload["objective"],
                payload["tone"],
                json.dumps(report),
                datetime.utcnow().isoformat(),
                source_payload["source_type"],
                source_payload["source_reference"],
                source_payload["uploaded_file"],
            ),
        )
        db.commit()
        flash("Analysis complete. Your short-form opportunities are ready.")
        return redirect(url_for("dashboard"))

    raw_generations = db.execute(
        "SELECT * FROM generations WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user["id"],)
    ).fetchall()

    generated: list[dict[str, Any]] = []
    for row in raw_generations:
        item = dict(row)
        try:
            item["report"] = json.loads(item["output"])
        except json.JSONDecodeError:
            item["report"] = {"source_content_summary": item["output"], "short_form_options": []}
        generated.append(item)

                output,
                datetime.utcnow().isoformat(),
            ),
        )
        db.commit()
        flash("Content generated successfully.")
        return redirect(url_for("dashboard"))

    package = PACKAGES.get(user["package_id"]) if user["package_id"] else None
    usage_count = db.execute(
        "SELECT COUNT(*) AS total FROM generations WHERE user_id = ?", (user["id"],)
    ).fetchone()["total"]
    return render_template(
        "dashboard.html",
        user=user,
        packages=PACKAGES,
        package=package,
        generated=generated,
        usage_count=usage_count,
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
