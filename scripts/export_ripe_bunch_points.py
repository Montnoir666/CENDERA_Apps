#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract just the Ripe Bunch detections from outputs/Bunch_development_synced.xlsx
into a small standalone file, ready to bring into QGIS as a point layer.

Writes both a .xlsx and a .csv (identical content) — the CSV is the one to
use for QGIS's "Add Delimited Text Layer" (simplest, most reliable way to
turn lat/lon columns into real point geometry).

    python scripts/export_ripe_bunch_points.py
"""

import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_XLSX = os.path.join(PROJECT_ROOT, "outputs", "Bunch_development_synced.xlsx")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
BUNCH_TYPE = "Ripe Bunch"
ESTATE = "Sungai Besar Jln 6 1_2"  # set to None to include every estate

COLUMNS = ["estate", "assessment_date", "latitude", "longitude", "confidence",
           "source_folder", "frame_filename"]


def main():
    if not os.path.exists(INPUT_XLSX):
        sys.exit(f"Cannot find {INPUT_XLSX}. Run build_bunch_development.py first.")
    df = pd.read_excel(INPUT_XLSX, sheet_name="detections")
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]
    df = df[df["detected_class"] == BUNCH_TYPE]
    if ESTATE is not None:
        df = df[df["estate"] == ESTATE]
    df = df[COLUMNS].sort_values(["estate", "assessment_date"]).reset_index(drop=True)

    if df.empty:
        sys.exit(f"No {BUNCH_TYPE} detections found.")

    print(f"{len(df)} {BUNCH_TYPE} points:")
    print(df.groupby("estate").size().to_string())

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_estate = ("_" + "".join(c if c.isalnum() else "_" for c in ESTATE).strip("_")) if ESTATE else ""
    xlsx_path = os.path.join(OUTPUT_DIR, f"Ripe_Bunch_points{safe_estate}.xlsx")
    csv_path = os.path.join(OUTPUT_DIR, f"Ripe_Bunch_points{safe_estate}.csv")
    df.to_excel(xlsx_path, index=False)
    df.to_csv(csv_path, index=False)
    print(f"\nWrote {xlsx_path}")
    print(f"Wrote {csv_path}  <- use this one in QGIS")


if __name__ == "__main__":
    main()
