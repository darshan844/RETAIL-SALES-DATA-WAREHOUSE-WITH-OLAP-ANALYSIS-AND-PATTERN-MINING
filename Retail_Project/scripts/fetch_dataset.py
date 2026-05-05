"""
Download UCI Online Retail (zip with .xlsx) and save data/Online_Retail.csv.

Use this if you do not already have the CSV. Requires: pip install openpyxl
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd


DEFAULT_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"


def project_data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


def download_and_convert(url: str, data_dir: Path) -> Path:
    import urllib.request

    data_dir.mkdir(parents=True, exist_ok=True)
    zip_path = data_dir / "online_retail.zip"
    print(f"Downloading: {url}")
    urllib.request.urlretrieve(url, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        xlsx_names = [n for n in zf.namelist() if n.lower().endswith(".xlsx")]
        if not xlsx_names:
            raise RuntimeError("No .xlsx file found inside the zip.")
        name = xlsx_names[0]
        print(f"Reading: {name}")
        with zf.open(name) as f:
            df = pd.read_excel(io.BytesIO(f.read()))

    out_csv = data_dir / "Online_Retail.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"Wrote {len(df):,} rows to {out_csv.resolve()}")
    return out_csv


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch Online Retail dataset from UCI.")
    p.add_argument("--url", default=DEFAULT_URL, help="Zip URL (UCI static file).")
    p.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Data folder (default: Retail_Project/data).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = args.output_dir or project_data_dir()
    try:
        download_and_convert(args.url, data_dir)
        return 0
    except Exception:
        print("Error:", sys.exc_info()[1])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
