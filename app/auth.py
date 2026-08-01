#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Editable, estate-scoped account store for CENDERA.

Locally, credentials live in accounts/users.xlsx (columns: username,
password, role, estates) so they can be added/edited/dropped in Excel
without touching the app. Run scripts/setup_accounts.py once to bootstrap
that file.

On a host like Render, accounts/users.xlsx is never deployed (it's
gitignored — plaintext passwords shouldn't go in git even in a private
repo). Instead, mount a "Secret File" named users.csv at
ACCOUNTS_SECRET_PATH (defaults to Render's own /etc/secrets/users.csv) with
the same four columns as a CSV. If that file exists, it's used instead of
the local xlsx — nothing else about auth changes.

Either way, the source is re-read on every login and every page load, so
edits — including revoking a user by deleting their row — take effect
immediately without restarting the server. No caching.

SECURITY NOTE: passwords are stored in PLAINTEXT, not hashed — that is the
deliberate tradeoff for "edit it like a spreadsheet." Treat whichever source
is active like any other secret; don't email it or leave it somewhere widely
readable.
"""

import csv
import os
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS_XLSX = os.path.join(PROJECT_ROOT, "accounts", "users.xlsx")
ACCOUNTS_SECRET_PATH = os.environ.get("ACCOUNTS_SECRET_PATH", "/etc/secrets/users.csv")


def _parse_estates(raw):
    raw = "" if raw is None else str(raw)
    return [e.strip() for e in raw.split(",") if e.strip()]


def _load_from_secret_csv(path):
    users = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            username = (row.get("username") or "").strip()
            if not username:
                continue
            users[username] = {
                "password": row.get("password") or "",
                "role": (row.get("role") or "user").strip().lower(),
                "estates": _parse_estates(row.get("estates")),
            }
    return users


def _load_from_xlsx(path):
    df = pd.read_excel(path, sheet_name="users")
    users = {}
    for _, r in df.iterrows():
        username = str(r.get("username", "")).strip()
        if not username or username.lower() == "nan":
            continue
        users[username] = {
            "password": "" if pd.isna(r.get("password")) else str(r.get("password")),
            "role": str(r.get("role", "user")).strip().lower(),
            "estates": _parse_estates(None if pd.isna(r.get("estates")) else r.get("estates")),
        }
    return users


def load_users():
    """Returns {username: {"password": str, "role": "admin"|"user", "estates": [str, ...]}}."""
    if os.path.exists(ACCOUNTS_SECRET_PATH):
        return _load_from_secret_csv(ACCOUNTS_SECRET_PATH)
    if os.path.exists(ACCOUNTS_XLSX):
        return _load_from_xlsx(ACCOUNTS_XLSX)
    return {}


def verify_login(username, password):
    user = load_users().get(username)
    if not user:
        return False
    return user["password"] == password


def get_user(username):
    if not username:
        return None
    return load_users().get(username)
