"""
STEP 6 — Frequent pattern mining (Apriori) + association rules.

Market-basket view:
  - Each invoice (InvoiceNo) is treated as one transaction.
  - Each line contributes an item (StockCode) to that basket.

Why Apriori:
  - Finds frequent itemsets under a minimum support threshold using the Apriori
    anti-monotone property (prunes infrequent supersets).

Association rules:
  - Derived from frequent itemsets; interpreted as conditional patterns A -> B.

Metrics (mlxtend):
  - support: P(A and B) for itemsets; rule support is support of the union itemset.
  - confidence: P(B | A) = support(A ∪ B) / support(A).
  - lift: confidence / P(B), measures dependence vs independence.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder


logger = logging.getLogger(__name__)


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def project_dirs() -> tuple[Path, Path, Path]:
    root = Path(__file__).resolve().parent.parent
    return root, root / "data", root / "results"


def load_cleaned(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Cleaned CSV not found: {path}")
    df = pd.read_csv(path, encoding="utf-8")
    needed = {"InvoiceNo", "StockCode"}
    missing = needed - set(df.columns)
    if missing:
        raise KeyError(f"Missing columns for baskets: {sorted(missing)}")
    return df


def build_transactions(df: pd.DataFrame) -> list[list[str]]:
    """
    Convert dataframe to a list of transactions (lists of item codes).

    We group by InvoiceNo and collect distinct StockCode values per invoice.
    """
    df = df.copy()
    df["StockCode"] = df["StockCode"].astype(str).str.strip()
    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()

    baskets: list[list[str]] = []
    for _, g in df.groupby("InvoiceNo", sort=False):
        items = sorted(set(g["StockCode"].tolist()))
        if len(items) >= 2:
            # Apriori needs multi-item baskets to produce rules with antecedent/consequent.
            baskets.append(items)
    logger.info("Built %s baskets with at least 2 items.", f"{len(baskets):,}")
    return baskets


def encode_transactions(baskets: list[list[str]]) -> tuple[pd.DataFrame, TransactionEncoder]:
    """One-hot encode baskets into a binary matrix for mlxtend."""
    te = TransactionEncoder()
    te_ary = te.fit_transform(baskets)
    dummies = pd.DataFrame(te_ary, columns=te.columns_)
    return dummies, te


def mine_patterns(
    dummies: pd.DataFrame,
    min_support: float,
    min_confidence: float,
    algorithm: str = "apriori",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Frequent itemsets via Apriori (candidate generation) or FP-Growth (tree-based).
    Rules use the same association_rules() step so metrics stay comparable.
    """
    if algorithm == "apriori":
        fi = apriori(dummies, min_support=min_support, use_colnames=True)
    else:
        fi = fpgrowth(dummies, min_support=min_support, use_colnames=True)

    logger.info("[%s] Frequent itemsets found: %s", algorithm, f"{len(fi):,}")

    if fi.empty:
        logger.warning("No frequent itemsets at this support threshold.")
        return fi, pd.DataFrame()

    rules = association_rules(
        fi,
        metric="confidence",
        min_threshold=min_confidence,
    )
    # lift is computed by mlxtend when possible; keep standard columns.
    if not rules.empty and "lift" not in rules.columns:
        logger.warning("Lift column missing; check mlxtend version.")

    rules = rules.sort_values(["lift", "confidence"], ascending=False)
    logger.info("Association rules generated: %s", f"{len(rules):,}")
    return fi, rules


def print_top_rules(rules: pd.DataFrame, n: int = 15) -> None:
    if rules.empty:
        print("\n(No rules to display — lower thresholds or verify baskets.)\n")
        return
    cols = [c for c in ["antecedents", "consequents", "support", "confidence", "lift"] if c in rules.columns]
    print("\nTop association rules (sorted by lift, then confidence):\n")
    print(rules[cols].head(n).to_string(index=False))
    print()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Apriori + association rules for retail baskets.")
    p.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Cleaned CSV (default: data/cleaned_retail_data.csv).",
    )
    p.add_argument(
        "--min-support",
        type=float,
        default=0.02,
        help="Minimum support for Apriori (default: 0.02).",
    )
    p.add_argument(
        "--min-confidence",
        type=float,
        default=0.5,
        help="Minimum confidence for association rules (default: 0.5).",
    )
    p.add_argument(
        "--algorithm",
        choices=("apriori", "fpgrowth"),
        default="apriori",
        help="Itemset mining algorithm (default: apriori). FP-Growth is often faster on dense data.",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    _root, data_dir, results_dir = project_dirs()
    results_dir.mkdir(parents=True, exist_ok=True)

    csv_path = args.csv or (data_dir / "cleaned_retail_data.csv")
    tag = "" if args.algorithm == "apriori" else f"{args.algorithm}_"
    out_rules = results_dir / f"{tag}association_rules.csv"
    out_items = results_dir / f"{tag}frequent_itemsets.csv"

    try:
        df = load_cleaned(csv_path)
        baskets = build_transactions(df)
        if not baskets:
            logger.error("No baskets built — check InvoiceNo/StockCode.")
            return 1

        dummies, _te = encode_transactions(baskets)
        fi, rules = mine_patterns(
            dummies,
            args.min_support,
            args.min_confidence,
            algorithm=args.algorithm,
        )

        fi.to_csv(out_items, index=False)
        rules.to_csv(out_rules, index=False)

        print_top_rules(rules, n=15)
        print(f">>> Saved frequent itemsets to: {out_items.resolve()}")
        print(f">>> Saved association rules to: {out_rules.resolve()}\n")
        return 0

    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    except KeyError as exc:
        logger.error("%s", exc)
        return 1
    except Exception:
        logger.exception("Pattern mining failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
