"""
STEP 7 — Visualization for exploratory analysis + pattern mining outputs.

Charts:
  1) Top 10 products by revenue (cleaned CSV)
  2) Monthly sales trend (cleaned CSV)
  3) Support distribution (association rules)
  4) Confidence distribution (association rules)
  5) Sales by country (cleaned CSV)

Outputs are written to results/charts/ for inclusion in the report.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
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


def project_paths() -> tuple[Path, Path, Path]:
    root = Path(__file__).resolve().parent.parent
    return root, root / "data", root / "results"


def ensure_charts_dir(results_dir: Path) -> Path:
    charts = results_dir / "charts"
    charts.mkdir(parents=True, exist_ok=True)
    return charts


def load_cleaned(csv_path: Path) -> pd.DataFrame:
    if not csv_path.is_file():
        raise FileNotFoundError(f"Cleaned CSV not found: {csv_path}")
    df = pd.read_csv(csv_path, encoding="utf-8")
    if "TotalAmount" not in df.columns:
        df["TotalAmount"] = df["Quantity"] * df["UnitPrice"]
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df = df.dropna(subset=["InvoiceDate"])
    return df


def chart_top10_products(df: pd.DataFrame, out_dir: Path) -> None:
    g = (
        df.groupby("StockCode", as_index=False)["TotalAmount"]
        .sum()
        .sort_values("TotalAmount", ascending=False)
        .head(10)
    )

    plt.figure(figsize=(10, 5))
    plt.bar(g["StockCode"].astype(str), g["TotalAmount"], color="#2E86AB")
    plt.title("Top 10 Products by Total Revenue")
    plt.xlabel("StockCode")
    plt.ylabel("Total revenue")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    path = out_dir / "top10_products_revenue.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logger.info("Saved %s", path.name)


def chart_monthly_trend(df: pd.DataFrame, out_dir: Path) -> None:
    x = df.copy()
    x["year_month"] = x["InvoiceDate"].dt.to_period("M").astype(str)
    m = x.groupby("year_month", as_index=False)["TotalAmount"].sum()

    plt.figure(figsize=(11, 5))
    plt.plot(m["year_month"], m["TotalAmount"], marker="o", color="#A23B72")
    plt.title("Monthly Sales Trend (TotalAmount)")
    plt.xlabel("Month")
    plt.ylabel("Total sales")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    path = out_dir / "monthly_sales_trend.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logger.info("Saved %s", path.name)


def chart_sales_by_country(df: pd.DataFrame, out_dir: Path) -> None:
    c = df.groupby("Country", as_index=False)["TotalAmount"].sum().sort_values("TotalAmount", ascending=False)

    plt.figure(figsize=(11, 5))
    plt.bar(c["Country"].astype(str), c["TotalAmount"], color="#F18F01")
    plt.title("Sales by Country")
    plt.xlabel("Country")
    plt.ylabel("Total sales")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    path = out_dir / "sales_by_country.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logger.info("Saved %s", path.name)


def chart_rule_metric_histogram(rules: pd.DataFrame, column: str, title: str, fname: str, out_dir: Path) -> None:
    if column not in rules.columns or rules.empty:
        logger.warning("Skipping %s chart (missing column or empty rules).", column)
        return
    plt.figure(figsize=(9, 5))
    plt.hist(rules[column].dropna(), bins=30, color="#6A994E", edgecolor="white")
    plt.title(title)
    plt.xlabel(column)
    plt.ylabel("Count")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    path = out_dir / fname
    plt.savefig(path, dpi=150)
    plt.close()
    logger.info("Saved %s", path.name)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate matplotlib charts for the retail project.")
    p.add_argument("--csv", type=Path, default=None, help="Cleaned CSV path.")
    p.add_argument(
        "--rules",
        type=Path,
        default=None,
        help="association_rules.csv path (default: results/association_rules.csv).",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    _root, data_dir, results_dir = project_paths()
    csv_path = args.csv or (data_dir / "cleaned_retail_data.csv")
    rules_path = args.rules or (results_dir / "association_rules.csv")
    charts_dir = ensure_charts_dir(results_dir)

    try:
        df = load_cleaned(csv_path)
        chart_top10_products(df, charts_dir)
        chart_monthly_trend(df, charts_dir)
        chart_sales_by_country(df, charts_dir)

        if rules_path.is_file():
            rules = pd.read_csv(rules_path)
            chart_rule_metric_histogram(
                rules,
                "support",
                "Distribution of Rule Support",
                "support_distribution.png",
                charts_dir,
            )
            chart_rule_metric_histogram(
                rules,
                "confidence",
                "Distribution of Rule Confidence",
                "confidence_distribution.png",
                charts_dir,
            )
        else:
            logger.warning("Rules file not found (%s). Run pattern_mining.py first.", rules_path)

        print(f"\n>>> Charts saved under: {charts_dir.resolve()}\n")
        return 0

    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    except Exception:
        logger.exception("Visualization failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
