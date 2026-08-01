#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared data-loading logic for the WC1 dashboard.

Used by both the Flask app (app/app.py) and the legacy static exporter
(scripts/build_dashboard.py).
"""

import math
import random
import sys
import os
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_XLSX = os.path.join(PROJECT_ROOT, "outputs", "WC1_agronomic_assessment_synced.xlsx")
WC1_COLORS = {
    "Nutrient Deficiency":            "#F2C200",
    "Pest & Disease":                 "#D7263D",
    "Frond Pruning/Canopy Condition": "#2E8B57",
    "Ground Condition":               "#1F6FEB",
    "Unclassified":                   "#888888",
}
DECLUTTER_RADIUS_M = 2.0


def declutter(markers, radius_m):
    groups = {}
    for m in markers:
        groups.setdefault((round(m["lat"], 5), round(m["lng"], 5)), []).append(m)
    for (lat0, _), grp in groups.items():
        if len(grp) < 2:
            grp[0]["dlat"], grp[0]["dlng"] = grp[0]["lat"], grp[0]["lng"]
            continue
        dlat = radius_m / 111320.0
        dlng = radius_m / (111320.0 * max(0.1, math.cos(math.radians(lat0))))
        for i, m in enumerate(grp):
            a = 2 * math.pi * i / len(grp)
            m["dlat"] = m["lat"] + dlat * math.sin(a)
            m["dlng"] = m["lng"] + dlng * math.cos(a)


def load_wc1(allowed_estates=None):
    """allowed_estates: None = no restriction (admin); else an iterable of
    estate names to keep (everything else is filtered out before markers,
    counts, dropdown estate/month lists, and the map center are computed)."""
    try:
        df = pd.read_excel(INPUT_XLSX, sheet_name="assessment")
    except FileNotFoundError:
        sys.exit(f"Cannot find {INPUT_XLSX}. Run build_wc1_assessment.py first.")
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]
    if allowed_estates is not None:
        df = df[df["estate"].isin(allowed_estates)]

    def c(v):
        return "" if pd.isna(v) else str(v)

    markers = []
    for _, r in df.iterrows():
        t = c(r.get("agronomic_assessment_type")).strip() or "Unclassified"
        if t not in WC1_COLORS:
            t = "Unclassified"
        markers.append({
            "lat": float(r["latitude"]), "lng": float(r["longitude"]),
            "type": t, "remarks": c(r.get("remarks")),
            "frame": c(r.get("frame_filename")), "video": c(r.get("video_filename")),
            "estate": c(r.get("estate")) or "Unassigned",
            "month": c(r.get("assessment_month")) or "unknown",
            "img": c(r.get("frame_relpath")), "dt": c(r.get("frame_absolute_datetime")),
        })
    declutter(markers, DECLUTTER_RADIUS_M)
    counts = {t: sum(1 for m in markers if m["type"] == t) for t in WC1_COLORS}
    counts = {t: n for t, n in counts.items() if n > 0}
    estates = sorted({m["estate"] for m in markers})
    months = sorted({m["month"] for m in markers})
    if len(df):
        center = {"lat": df["latitude"].mean(), "lng": df["longitude"].mean()}
    else:
        center = {"lat": 0.0, "lng": 0.0}
    return markers, counts, estates, months, center


def mock_bunch(center):
    random.seed(42)
    stages = [("Early (green)", 22, 45), ("Developing", 11, 21),
              ("Near-ripe", 4, 10), ("Ripe now", 0, 3)]
    out = []
    for i in range(30):
        name, lo, hi = random.choice(stages)
        out.append({"lat": center["lat"] + random.uniform(-0.0012, 0.0012),
                    "lng": center["lng"] + random.uniform(-0.0012, 0.0012),
                    "stage": name, "days": random.randint(lo, hi), "palm": f"P{i+1:03d}"})
    return out


def mock_yield(center):
    random.seed(7)
    return [{"lat": center["lat"] + random.uniform(-0.0013, 0.0013),
             "lng": center["lng"] + random.uniform(-0.0013, 0.0013),
             "palm": f"P{i+1:03d}", "yield_kg": round(random.uniform(80, 220), 1)}
            for i in range(40)]
