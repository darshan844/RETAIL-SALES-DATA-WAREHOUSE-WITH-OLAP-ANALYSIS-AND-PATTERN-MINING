"""
STEP 2 — Data cleaning for Online Retail–style transaction CSV.

Why cleaning matters:
  - Missing values break joins and distort aggregates.
  - Duplicates inflate counts and revenue.
  - Negative quantities are typically cancellations/returns and are excluded for a
    simple sales-focused mart (can be modeled separately in a full production system).
  - Parsing dates enables time-based OLAP and trend analysis.
  - TotalAmount is a derived measure used in fact loading and visualization.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd


logger = logging.getLogger(__name__)


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def project_data_dir() -> Path:
    """Resolve ../data relative to this script (Retail_Project/data/)."""
    return Path(__file__).resolve().parent.parent / "data"


def load_raw_csv(input_path: Path) -> pd.DataFrame:
    """Load CSV; try UTF-8 first, then latin-1 (common for UCI exports)."""
    if not input_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    try:
        df = pd.read_csv(input_path, encoding="utf-8")
    except UnicodeDecodeError:
        logger.warning("UTF-8 failed; reading with latin-1.")
        df = pd.read_csv(input_path, encoding="latin-1")

    logger.info("Loaded raw data: %s rows, %s columns.", f"{len(df):,}", len(df.columns))
    return df


def print_summary(df: pd.DataFrame, title: str) -> None:
    """Human-readable dataset summary for notebooks/reports."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print("\nColumn dtypes:\n", df.dtypes)
    print("\nMissing values per column:\n", df.isna().sum())
    print("\nFirst 5 rows:\n", df.head())
    print("=" * 70 + "\n")


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleaning pipeline (transformation logic):
      1) dropna: listwise deletion for a complete-case analytical extract
      2) drop_duplicates: remove identical rows
      3) Quantity > 0: keep valid sales lines
      4) parse InvoiceDate to datetime (UK-style day-first is typical for this dataset)
      5) compute TotalAmount measure
    """
    n0 = len(df)

    # Remove missing values — incomplete rows cannot be joined reliably to dimensions.
    df1 = df.dropna().copy()
    logger.info("After dropna: %s rows (removed %s).", f"{len(df1):,}", f"{n0 - len(df1):,}")

    # Remove exact duplicate records.
    df2 = df1.drop_duplicates()
    logger.info("After drop_duplicates: %s rows (removed %s).", f"{len(df2):,}", f"{len(df1) - len(df2):,}")

    # Filter negative or zero quantities (returns/cancellations) for a sales-only mart.
    if "Quantity" not in df2.columns:
        raise KeyError("Column 'Quantity' is required.")
    df3 = df2[df2["Quantity"] > 0].copy()
    logger.info("After Quantity > 0: %s rows (removed %s).", f"{len(df3):,}", f"{len(df2) - len(df3):,}")

    # Parse invoice date — required for Time_Dim and monthly trends.
    if "InvoiceDate" not in df3.columns:
        raise KeyError("Column 'InvoiceDate' is required.")
    # Excel → CSV often yields mixed date strings; let pandas infer (avoid dayfirst=True-only bias).
    df3["InvoiceDate"] = pd.to_datetime(df3["InvoiceDate"], errors="coerce")
    bad_dates = df3["InvoiceDate"].isna().sum()
    if bad_dates:
        logger.warning("Dropping %s rows with invalid InvoiceDate.", int(bad_dates))
        df3 = df3.dropna(subset=["InvoiceDate"])

    # Derived measure used in fact table revenue analysis.
    if "UnitPrice" not in df3.columns:
        raise KeyError("Column 'UnitPrice' is required.")
    df3["TotalAmount"] = df3["Quantity"] * df3["UnitPrice"]

    # Light normalization for stable string keys in SQL loads.
    for col in ("InvoiceNo", "StockCode", "Description", "Country"):
        if col in df3.columns:
            df3[col] = df3[col].astype(str).str.strip()

    logger.info("Cleaning complete. Final rows: %s", f"{len(df3):,}")
    return df3


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Clean Online Retail CSV for DW + mining.")
    p.add_argument(
        "-i",
        "--input",
        type=Path,
        default=None,
        help="Path to raw CSV (default: data/Online_Retail.csv).",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Path to cleaned CSV (default: data/cleaned_retail_data.csv).",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    data_dir = project_data_dir()
    input_path = args.input or (data_dir / "Online_Retail.csv")
    output_path = args.output or (data_dir / "cleaned_retail_data.csv")

    try:
        raw = load_raw_csv(input_path)
        print_summary(raw, "RAW DATASET SUMMARY")

        cleaned = clean_dataframe(raw)
        print_summary(cleaned, "CLEANED DATASET SUMMARY")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cleaned.to_csv(output_path, index=False, encoding="utf-8")

        print(f"\n>>> Cleaning complete. Saved: {output_path.resolve()}\n")
        return 0

    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    except KeyError as exc:
        logger.error("Missing required column: %s", exc)
        return 1
    except Exception:
        logger.exception("Unexpected error during cleaning.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
