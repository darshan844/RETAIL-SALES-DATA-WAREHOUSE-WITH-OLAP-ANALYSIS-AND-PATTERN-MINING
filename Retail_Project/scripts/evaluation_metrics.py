"""
STEP 8 — Evaluation summary for frequent itemsets + association rules.

Reads outputs produced by pattern_mining.py and prints aggregate statistics:
  - counts of itemsets/rules
  - mean support / confidence / lift across rules

This supports the "results evaluation" section of the academic report.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
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


def project_results_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "results"


def summarize(results_dir: Path, algorithm: str = "apriori") -> None:
    tag = "" if algorithm == "apriori" else "fpgrowth_"
    fi_path = results_dir / f"{tag}frequent_itemsets.csv"
    rules_path = results_dir / f"{tag}association_rules.csv"

    print("\n" + "=" * 70)
    print("PATTERN MINING — EVALUATION SUMMARY")
    print(f"(files: {algorithm})")
    print("=" * 70)

    if fi_path.is_file():
        fi = pd.read_csv(fi_path)
        print(f"\nFrequent itemsets: {len(fi):,}")
        if "support" in fi.columns:
            print(f"  - mean itemset support: {float(fi['support'].mean()):.6f}")
            print(f"  - max  itemset support: {float(fi['support'].max()):.6f}")
    else:
        print(f"\nFrequent itemsets file not found: {fi_path}")
        print("Run: python scripts/pattern_mining.py")

    if rules_path.is_file():
        rules = pd.read_csv(rules_path)
        print(f"\nAssociation rules: {len(rules):,}")
        if not rules.empty:
            if "support" in rules.columns:
                print(f"  - average support:    {float(np.mean(rules['support'])):.6f}")
            if "confidence" in rules.columns:
                print(f"  - average confidence: {float(np.mean(rules['confidence'])):.6f}")
            if "lift" in rules.columns:
                print(f"  - average lift:       {float(np.mean(rules['lift'])):.6f}")
    else:
        print(f"\nAssociation rules file not found: {rules_path}")
        print("Run: python scripts/pattern_mining.py")

    print("\n" + "=" * 70 + "\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize pattern mining outputs.")
    p.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="Folder containing frequent_itemsets*.csv and association_rules*.csv.",
    )
    p.add_argument(
        "--algorithm",
        choices=("apriori", "fpgrowth"),
        default="apriori",
        help="Which mining run to evaluate (must match pattern_mining filenames).",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)
    results_dir = args.results_dir or project_results_dir()

    if not results_dir.is_dir():
        logger.error("Results directory not found: %s", results_dir)
        return 1

    try:
        summarize(results_dir, algorithm=args.algorithm)
        return 0
    except Exception:
        logger.exception("Evaluation failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
