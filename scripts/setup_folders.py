#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create the standalone dashboard project structure.

Run once from anywhere:
    python scripts/setup_folders.py

Creates (at the project root, regardless of current directory):
    data/Rembau/   data/Setiawan/   data/Serdang/
    outputs/

Then COPY each flight folder AND its matching _frame_metadata.csv into the
correct estate folder, e.g.
    data/Serdang/DJI_20260113101712_0103_D/
    data/Serdang/DJI_20260113101712_0103_D_frame_metadata.csv
Copying (not just referencing) keeps this dashboard fully self-contained.
(You may add month subfolders if you like; month is derived from the flight date.)
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESTATES = ["Rembau", "Setiawan", "Serdang"]  # add/rename freely


def main():
    for e in ESTATES:
        os.makedirs(os.path.join(PROJECT_ROOT, "data", e), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "outputs"), exist_ok=True)
    print("Created:")
    for e in ESTATES:
        print(f"  data/{e}/")
    print("  outputs/")
    print("\nNext: move each DJI_* folder + its _frame_metadata.csv into the "
          "matching data/<estate>/ folder, then run build_wc1_assessment.py")


if __name__ == "__main__":
    main()
