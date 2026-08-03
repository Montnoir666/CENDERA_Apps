#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flight telemetry loading + per-flight aggregation.

Telemetry lives in data/Flight Telemetry/<estate>/*.xlsx (raw DJI flight-log
exports, one row per ~0.1s of flight). This matches those rows to the
DJI_<date><time>_<seq>_D flight folders used by build_wc1_assessment.py /
core/dashboard_data.py, keyed on the date+time embedded in both naming
schemes:

    Telemetry Source_File: DJIFlightRecord_YYYY-MM-DD_[HH-MM-SS]-aircraft.csv
    Flight folder:         DJI_YYYYMMDDHHMMSS_<seq>_D

Only flights that already have real assessment data (i.e. appear in
outputs/WC1_agronomic_assessment_synced.xlsx's flight_counts sheet) are
summarized — telemetry for flights with no matching assessment data yet
(e.g. later, unreviewed flights) is intentionally left out.
"""

import os
import re
import glob
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TELEMETRY_DIR = os.path.join(PROJECT_ROOT, "data", "Flight Telemetry")
OUTPUT_XLSX = os.path.join(PROJECT_ROOT, "outputs", "WC1_agronomic_assessment_synced.xlsx")

_SRC_RE = re.compile(r"DJIFlightRecord_(\d{4})-(\d{2})-(\d{2})_\[(\d{2})-(\d{2})-(\d{2})\]")
_FOLDER_RE = re.compile(r"DJI_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})_")


def _source_file_key(name):
    m = _SRC_RE.search(str(name))
    return "".join(m.groups()) if m else None


def _folder_key(folder_name):
    m = _FOLDER_RE.match(str(folder_name))
    return "".join(m.groups()) if m else None


def load_telemetry(estate):
    """Returns {datetime_key: {duration_s, height_avg_m, height_max_m,
    speed_avg_ms, signal_avg_pct}} for one estate, or {} if none found."""
    est_dir = os.path.join(TELEMETRY_DIR, estate)
    if not os.path.isdir(est_dir):
        return {}
    files = glob.glob(os.path.join(est_dir, "*.xlsx"))
    if not files:
        return {}
    df = pd.concat([pd.read_excel(f) for f in files], ignore_index=True)
    df["_key"] = df["Source_File"].map(_source_file_key)
    df = df.dropna(subset=["_key"])

    out = {}
    for key, g in df.groupby("_key"):
        out[key] = {
            "duration_s": float(g["Time_s"].max() - g["Time_s"].min()),
            "height_avg_m": float(g["Height_m"].mean()),
            "height_max_m": float(g["Height_m"].max()),
            "speed_avg_ms": float(g["Speed_ms"].mean()),
            "signal_avg_pct": float(g["Signal_Video"].mean()),
        }
    return out


def load_frame_counts(estate=None):
    """Returns {source_folder: {"captured": int, "retained": int}} from the
    flight_counts sheet, optionally filtered to one estate."""
    if not os.path.exists(OUTPUT_XLSX):
        return {}
    df = pd.read_excel(OUTPUT_XLSX, sheet_name="flight_counts")
    if estate is not None:
        df = df[df["estate"] == estate]
    return {
        r["source_folder"]: {"captured": int(r["frames_captured"]), "retained": int(r["frames_retained"])}
        for _, r in df.iterrows()
    }


def flight_summary(estate):
    """One row per already-assessed flight for this estate, telemetry
    fields filled in where a match exists, sorted chronologically."""
    frame_counts = load_frame_counts(estate)
    telemetry = load_telemetry(estate)

    rows = []
    for name in sorted(frame_counts):
        key = _folder_key(name)
        t = telemetry.get(key, {})
        m = _FOLDER_RE.match(name)
        date_str = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
        time_str = f"{m.group(4)}:{m.group(5)}:{m.group(6)}" if m else ""
        rows.append({
            "flight": name,
            "date": date_str,
            "time": time_str,
            "duration_min": round(t["duration_s"] / 60, 1) if t else None,
            "height_avg_m": round(t["height_avg_m"], 1) if t else None,
            "height_max_m": round(t["height_max_m"], 1) if t else None,
            "speed_avg_ms": round(t["speed_avg_ms"], 2) if t else None,
            "signal_avg_pct": round(t["signal_avg_pct"], 1) if t else None,
            "frames_captured": frame_counts[name]["captured"],
            "frames_retained": frame_counts[name]["retained"],
        })
    return rows
