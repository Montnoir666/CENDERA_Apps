#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CENDERA — by Cendera Technologies

Login-gated Flask app serving the Agronomic Assessment / Bunch Development /
Yield Map dashboard. Config comes from environment variables (see .env.example) and
accounts/users.xlsx (see auth.py) so the same code can later run on a remote
host without changes.

    pip install -r requirements.txt
    cd "C:\\Documents\\oil_palm_dashboard\\oil_palm_dashboard"
    python app/app.py
    -> http://localhost:5000
"""

import os
import sys
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect, url_for, session,
    send_from_directory, abort,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import auth
from core import dashboard_data as dd

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-change-me")

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
DATA_ROOT = os.path.join(PROJECT_ROOT, "data", "Agronomic Assessment")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = auth.get_user(session.get("user"))
        if not user:
            session.clear()
            return redirect(url_for("login", next=request.path))
        return view(user, *args, **kwargs)
    return wrapped


def allowed_estates_for(user):
    """None means unrestricted (admin)."""
    return None if user["role"] == "admin" else user["estates"]


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if auth.verify_login(username, password):
            session["user"] = username
            return redirect(request.args.get("next") or url_for("index"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index(user):
    allowed = allowed_estates_for(user)
    wc1, counts, estates, months, center = dd.load_wc1(allowed_estates=allowed)
    scope_label = "All estates" if allowed is None else (", ".join(allowed) or "No estates assigned")
    return render_template(
        "dashboard.html",
        username=session["user"],
        scope_label=scope_label,
        api_key=GOOGLE_MAPS_API_KEY,
        wc1_colors=dd.WC1_COLORS,
        wc1_markers=wc1,
        wc1_counts=counts,
        estates=estates,
        months=months,
        bunch_markers=dd.mock_bunch(center),
        yield_markers=dd.mock_yield(center),
        center=center,
    )


@app.route("/media/<path:filepath>")
@login_required
def media(user, filepath):
    allowed = allowed_estates_for(user)
    if allowed is not None:
        estate = filepath.split("/", 1)[0]
        if estate not in allowed:
            abort(404)
    full = os.path.abspath(os.path.join(DATA_ROOT, filepath))
    if not full.startswith(DATA_ROOT + os.sep):
        abort(404)
    directory, filename = os.path.split(full)
    return send_from_directory(directory, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    if not os.path.exists(auth.ACCOUNTS_XLSX):
        print(f"WARNING: {auth.ACCOUNTS_XLSX} not found — run "
              f"scripts/setup_accounts.py first, or nobody will be able to log in.")
    if not GOOGLE_MAPS_API_KEY:
        print("WARNING: GOOGLE_MAPS_API_KEY is not set — set it in .env "
              "(see .env.example) or the map won't load.")
    app.run(host="0.0.0.0", port=port, debug=debug)
