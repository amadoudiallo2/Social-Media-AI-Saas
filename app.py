from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "saas.db"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret")

PACKAGES = {
    "starter": {
        "name": "Starter",
        "price": 29,
        "description": "Good for solopreneurs creating posts and captions.",
        "limit": 25,
    },
    "pro": {
        "name": "Pro",
        "price": 99,
        "description": "Unlimited text + image ideas and short-form video concepts.",
        "limit": -1,
    },
    "agency": {
        "name": "Agency",
        "price": 249,
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


def generate_marketing_content(payload: dict[str, Any]) -> str:
    business = payload["business_name"]
    audience = payload["audience"]
    objective = payload["objective"]
    tone = payload["tone"]
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
