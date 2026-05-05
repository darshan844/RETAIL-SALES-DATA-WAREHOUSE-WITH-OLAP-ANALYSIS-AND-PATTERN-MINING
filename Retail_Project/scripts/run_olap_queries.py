"""
Run OLAP queries from database/olap_queries.sql via Python.

Why this script:
  - Lets you execute all analytical queries after ETL without opening MySQL Workbench.
  - Optional CSV export for tables/figures in your report.

The database name should match the one in your MySQL URL (e.g. .../retail_dw).
USE statements in the SQL file are ignored here because the engine URL selects the schema.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


logger = logging.getLogger(__name__)


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_query_statements(sql_path: Path) -> list[str]:
    """
    Parse olap_queries.sql into executable SELECT statements.

    Strips USE ...; and full-line -- comments so drivers do not receive empty batches.
    """
    if not sql_path.is_file():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    raw = sql_path.read_text(encoding="utf-8")
    raw = re.sub(r"USE\s+[\w`]+\s*;", "", raw, flags=re.IGNORECASE)

    lines: list[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("--"):
            continue
        lines.append(line)

    blob = "\n".join(lines)
    parts = [p.strip() for p in blob.split(";") if p.strip()]
    selects = [p for p in parts if re.match(r"^\s*SELECT\b", p, re.IGNORECASE)]
    if not selects:
        raise ValueError("No SELECT statements found after parsing olap_queries.sql.")
    return selects


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Execute OLAP SQL queries and print results.")
    p.add_argument(
        "--mysql-url",
        type=str,
        required=True,
        help="SQLAlchemy URL, e.g. mysql+pymysql://user:pass@127.0.0.1:3306/retail_dw",
    )
    p.add_argument(
        "--sql-file",
        type=Path,
        default=None,
        help="Path to olap_queries.sql (default: database/olap_queries.sql).",
    )
    p.add_argument(
        "--save-csv",
        action="store_true",
        help="Save each result to results/olap/ as query_01.csv, ...",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    root = project_root()
    sql_path = args.sql_file or (root / "database" / "olap_queries.sql")
    out_dir = root / "results" / "olap"

    try:
        statements = load_query_statements(sql_path)
        engine = create_engine(args.mysql_url)

        for i, stmt in enumerate(statements, start=1):
            title = f"Query {i}/{len(statements)}"
            print("\n" + "=" * 72)
            print(title)
            print("=" * 72)
            df = pd.read_sql(text(stmt), engine)
            print(df.to_string(index=False))
            print(f"\nRows: {len(df):,}")

            if args.save_csv:
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"query_{i:02d}.csv"
                df.to_csv(out_path, index=False, encoding="utf-8")
                logger.info("Wrote %s", out_path)

        print("\n>>> Finished running OLAP queries.\n")
        return 0

    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    except ValueError as exc:
        logger.error("%s", exc)
        return 1
    except Exception:
        logger.exception("Failed to run OLAP queries.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
