#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Push accounts/users.xlsx to CENDERA's live Render deployment.

Local edits to accounts/users.xlsx never touch git (plaintext passwords),
so Render only ever sees the "users.csv" Secret File content you paste into
its dashboard. This script automates that paste: it converts the current
users.xlsx into CSV, pushes it to Render via the API, then triggers a
redeploy (Render doesn't hot-swap secret file content into an already
running instance, so a redeploy is required for the change to take effect).

One-time setup — add to .env (see .env.example):
    RENDER_API_KEY     Render dashboard -> Account Settings -> API Keys -> Create API Key
    RENDER_SERVICE_ID  the "srv-..." id, visible in the service's dashboard URL
                        (dashboard.render.com/web/<this-id>)

    python scripts/sync_accounts_to_render.py
"""

import io
import os
import sys

import pandas as pd
import requests
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS_XLSX = os.path.join(PROJECT_ROOT, "accounts", "users.xlsx")
SECRET_FILENAME = "users.csv"
API_BASE = "https://api.render.com/v1"
COLUMNS = ["username", "password", "role", "estates"]

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def build_csv():
    df = pd.read_excel(ACCOUNTS_XLSX, sheet_name="users")
    df = df.reindex(columns=COLUMNS).fillna("")
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def main():
    api_key = os.environ.get("RENDER_API_KEY")
    service_id = os.environ.get("RENDER_SERVICE_ID")
    if not api_key or not service_id:
        sys.exit(
            "Set RENDER_API_KEY and RENDER_SERVICE_ID in .env first "
            "(see .env.example for where to find each)."
        )
    if not os.path.exists(ACCOUNTS_XLSX):
        sys.exit(f"Cannot find {ACCOUNTS_XLSX}.")

    csv_content = build_csv()
    n_accounts = max(0, csv_content.count("\n") - 1)
    headers = {"Authorization": f"Bearer {api_key}"}

    r = requests.put(
        f"{API_BASE}/services/{service_id}/secret-files/{SECRET_FILENAME}",
        headers=headers,
        json={"content": csv_content},
        timeout=30,
    )
    if r.status_code not in (200, 201):
        sys.exit(f"Failed to update secret file: {r.status_code} {r.text}")
    print(f"Updated Render secret file '{SECRET_FILENAME}' ({n_accounts} accounts).")

    r2 = requests.post(
        f"{API_BASE}/services/{service_id}/deploys",
        headers=headers,
        json={},
        timeout=30,
    )
    if r2.status_code not in (200, 201, 202):
        sys.exit(f"Secret file updated, but failed to trigger redeploy: "
                  f"{r2.status_code} {r2.text}\nTrigger one manually from the Render dashboard.")
    print("Triggered a redeploy so the change takes effect — check Render's Events tab.")


if __name__ == "__main__":
    main()
