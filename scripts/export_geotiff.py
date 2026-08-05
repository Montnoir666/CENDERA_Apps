#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export bunch-detection points as a georeferenced GeoTIFF, for loading as a
custom map in Avenza Maps (or any other GIS app).

Reads outputs/Bunch_development_synced.xlsx, filters to one estate + bunch
type, and rasterizes each detection as a small dot at its real GPS
position. The output is a standard GeoTIFF (WGS84 / EPSG:4326, RGBA,
transparent background) — Avenza reads the embedded georeferencing
directly, no world file needed.

Edit ESTATE / BUNCH_TYPE below and re-run for a different export.

Needs rasterio, which isn't part of the live app's requirements.txt (this
script only ever runs offline, so it doesn't need to ship to Render):

    pip install rasterio
    python scripts/export_geotiff.py
"""

import os
import sys
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_bounds
from PIL import Image, ImageDraw

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_XLSX = os.path.join(PROJECT_ROOT, "outputs", "Bunch_development_synced.xlsx")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")

ESTATE = "Sungai Besar Jln 6 1_2"
BUNCH_TYPE = "Ripe Bunch"
POINT_COLOR = (215, 38, 61, 255)   # #D7263D, matches the dashboard's Ripe Bunch color
OUTLINE_COLOR = (255, 255, 255, 255)
POINT_RADIUS_M = 1.5               # on-the-ground radius of each dot
PADDING_FRAC = 0.15                # extra margin around the points' bounding box
TARGET_LONG_SIDE_PX = 2000         # resolution of the longer image side


def main():
    if not os.path.exists(INPUT_XLSX):
        sys.exit(f"Cannot find {INPUT_XLSX}. Run build_bunch_development.py first.")
    df = pd.read_excel(INPUT_XLSX, sheet_name="detections")
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]
    df = df[(df["estate"] == ESTATE) & (df["detected_class"] == BUNCH_TYPE)]
    if df.empty:
        sys.exit(f"No {BUNCH_TYPE} detections found for estate '{ESTATE}'.")
    print(f"{len(df)} {BUNCH_TYPE} points for {ESTATE}")

    lat_min, lat_max = df["latitude"].min(), df["latitude"].max()
    lng_min, lng_max = df["longitude"].min(), df["longitude"].max()
    lat_pad = (lat_max - lat_min) * PADDING_FRAC or 0.0002
    lng_pad = (lng_max - lng_min) * PADDING_FRAC or 0.0002
    west, east = lng_min - lng_pad, lng_max + lng_pad
    south, north = lat_min - lat_pad, lat_max + lat_pad

    # meters-per-degree at this latitude, to size the raster + the dots
    lat_mid = (south + north) / 2
    m_per_deg_lat = 111320.0
    m_per_deg_lng = 111320.0 * np.cos(np.radians(lat_mid))
    width_m = (east - west) * m_per_deg_lng
    height_m = (north - south) * m_per_deg_lat

    if width_m >= height_m:
        width_px = TARGET_LONG_SIDE_PX
        height_px = max(1, round(TARGET_LONG_SIDE_PX * height_m / width_m))
    else:
        height_px = TARGET_LONG_SIDE_PX
        width_px = max(1, round(TARGET_LONG_SIDE_PX * width_m / height_m))

    transform = from_bounds(west, south, east, north, width_px, height_px)
    px_per_m = width_px / width_m
    radius_px = max(3, round(POINT_RADIUS_M * px_per_m))

    img = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for _, r in df.iterrows():
        col, row = ~transform * (r["longitude"], r["latitude"])
        col, row = int(round(col)), int(round(row))
        bbox = [col - radius_px, row - radius_px, col + radius_px, row + radius_px]
        draw.ellipse(bbox, fill=POINT_COLOR, outline=OUTLINE_COLOR, width=max(1, radius_px // 4))

    arr = np.array(img)  # (H, W, 4) -> rasterio wants (bands, H, W)
    bands = np.moveaxis(arr, -1, 0)

    safe_estate = "".join(c if c.isalnum() else "_" for c in ESTATE).strip("_")
    safe_type = "".join(c if c.isalnum() else "_" for c in BUNCH_TYPE).strip("_")
    out_path = os.path.join(OUTPUT_DIR, f"{safe_estate}_{safe_type}_points.tiff")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with rasterio.open(
        out_path, "w", driver="GTiff",
        height=height_px, width=width_px, count=4, dtype="uint8",
        crs="EPSG:4326", transform=transform,
        photometric="RGB", alpha="yes", compress="deflate",
    ) as dst:
        dst.write(bands)

    print(f"Wrote {out_path} ({width_px}x{height_px}px, ~{width_m:.0f}m x {height_m:.0f}m)")


if __name__ == "__main__":
    main()
