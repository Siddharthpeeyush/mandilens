#!/usr/bin/env python3
"""Clean raw daily mandi CSVs into one tidy processed dataset.

Reads : data/raw/mandi_prices_*.csv
Writes: data/processed/mandi_prices_clean.csv
"""
import glob
import os
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED = os.path.join(BASE_DIR, "data", "processed",
                         "mandi_prices_clean.csv")


def main():
    files = sorted(glob.glob(os.path.join(RAW_DIR, "mandi_prices_*.csv")))
    if not files:
        print("CLEAN: no raw files found", file=sys.stderr)
        return 1
    frames = []
    for path in files:
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            print(f"CLEAN: skipping {path}: {exc}", file=sys.stderr)
            continue
        df.columns = [c.strip().lower() for c in df.columns]
        df["source_file"] = os.path.basename(path)
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)

    for col in ["state", "district", "market", "commodity", "variety", "grade"]:
        if col in data.columns:
            data[col] = data[col].astype(str).str.strip().str.title()
    for col in ["min_price", "max_price", "modal_price"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data["arrival_date"] = pd.to_datetime(data["arrival_date"],
                                         format="%d/%m/%Y", errors="coerce")

    data = data.dropna(subset=["modal_price", "arrival_date",
                               "market", "commodity"])
    data = data[(data["modal_price"] > 0) & (data["modal_price"] < 100000)]
    data = data.drop_duplicates(subset=["state", "district", "market",
                                        "commodity", "variety", "arrival_date"])
    data = data.sort_values(["arrival_date", "state", "market",
                             "commodity"]).reset_index(drop=True)

    os.makedirs(os.path.dirname(PROCESSED), exist_ok=True)
    data.to_csv(PROCESSED, index=False)
    print(f"CLEAN: {len(data)} rows, {data['market'].nunique()} markets, "
          f"{data['commodity'].nunique()} commodities -> {PROCESSED}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
