"""
STEP 4 — ETL: load cleaned_retail_data.csv into MySQL star schema.

Process overview:
  1) Connect to MySQL and optionally apply schema.sql (if tables missing).
  2) Clear fact/dimensions safely for a repeatable student demo (--reset).
  3) Populate dimensions (Time, Product, Customer) with de-duplication.
  4) Insert Sales_Fact rows with surrogate Time_ID lookups.
  5) Commit transaction and report row counts.

Duplicate-safe loads:
  - Dimensions use INSERT ... ON DUPLICATE KEY UPDATE where natural keys collide.
  - Fact insert assumes a clean fact table after reset (recommended for POC).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine


logger = logging.getLogger(__name__)


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def project_paths() -> tuple[Path, Path]:
    """Return (Retail_Project_root, data_dir)."""
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    return root, data_dir


def split_sql_statements(sql_text: str) -> list[str]:
    """Split DDL script on ';' (sufficient for our schema.sql)."""
    lines: list[str] = []
    for line in sql_text.splitlines():
        s = line.strip()
        if not s or s.startswith("--"):
            continue
        lines.append(line)
    blob = "\n".join(lines)
    return [p.strip() for p in blob.split(";") if p.strip()]


def run_schema_sql(engine: Engine, schema_path: Path) -> None:
    if not schema_path.is_file():
        raise FileNotFoundError(f"schema.sql not found: {schema_path}")
    stmts = split_sql_statements(schema_path.read_text(encoding="utf-8"))
    logger.info("Executing %s DDL statements from %s", len(stmts), schema_path.name)
    with engine.begin() as conn:
        for stmt in stmts:
            try:
                conn.execute(text(stmt))
            except Exception as exc:
                # Idempotency guard: repeated --init can hit existing index names.
                msg = str(exc).lower()
                if "duplicate key name" in msg or "(1061" in msg:
                    logger.warning("Skipping existing index while initializing schema: %s", stmt)
                    continue
                raise


def tables_exist(engine: Engine) -> bool:
    insp = inspect(engine)
    # Normalize for environments that expose lowercase table names.
    names = {n.lower() for n in insp.get_table_names()}
    return {"time_dim", "product_dim", "customer_dim", "sales_fact"} <= names


def truncate_all(engine: Engine) -> None:
    """Remove all rows in FK-safe order for MySQL."""
    logger.info("Truncating warehouse tables (reset)...")
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for tbl in ("Sales_Fact", "Time_Dim", "Product_Dim", "Customer_Dim"):
            conn.execute(text(f"TRUNCATE TABLE {tbl}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def normalize_customer_id(series: pd.Series) -> pd.Series:
    """Normalize CustomerID to a stable string for Customer_Dim primary key."""

    def _one(val: object) -> str:
        if pd.isna(val):
            return ""
        if isinstance(val, float) and float(val).is_integer():
            return str(int(val))
        s = str(val).strip()
        if s.endswith(".0") and s[:-2].isdigit():
            return s[:-2]
        return s

    return series.map(_one)


def load_cleaned_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Cleaned CSV not found: {path}")
    df = pd.read_csv(path, encoding="utf-8")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df = df.dropna(subset=["InvoiceDate"])
    for col in ("InvoiceNo", "StockCode", "Description", "Country"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    df["CustomerID_str"] = normalize_customer_id(df["CustomerID"])
    if "TotalAmount" not in df.columns:
        df["TotalAmount"] = df["Quantity"] * df["UnitPrice"]
    return df


def upsert_time_dim(engine: Engine, df: pd.DataFrame) -> pd.DataFrame:
    """Build unique calendar days and insert into Time_Dim; return mapping dataframe."""
    dt = df["InvoiceDate"].dt.normalize()
    days = pd.to_datetime(dt.unique())
    rows = []
    for d in days:
        ts = pd.Timestamp(d)
        rows.append(
            {
                "Date": ts.date(),
                "Month": int(ts.month),
                "Year": int(ts.year),
            }
        )
    tdf = pd.DataFrame(rows).drop_duplicates(subset=["Date"]).sort_values("Date")

    # Duplicate-safe dimension load
    with engine.begin() as conn:
        for _, r in tdf.iterrows():
            conn.execute(
                text(
                    """
                    INSERT INTO Time_Dim (`Date`, Month, Year)
                    VALUES (:d, :m, :y)
                    ON DUPLICATE KEY UPDATE Month = VALUES(Month), Year = VALUES(Year)
                    """
                ),
                {"d": r["Date"], "m": int(r["Month"]), "y": int(r["Year"])},
            )

    tmap = pd.read_sql(text("SELECT Time_ID, `Date` FROM Time_Dim"), engine)
    tmap["Date"] = pd.to_datetime(tmap["Date"]).dt.normalize()
    return tmap


def upsert_product_dim(engine: Engine, df: pd.DataFrame) -> None:
    """One Product_ID per StockCode."""
    g = df.sort_values("StockCode").groupby("StockCode", as_index=False).first()
    prod = g[["StockCode", "Description"]].rename(
        columns={"StockCode": "Product_ID", "Description": "Product_Name"}
    )
    with engine.begin() as conn:
        for _, r in prod.iterrows():
            conn.execute(
                text(
                    """
                    INSERT INTO Product_Dim (Product_ID, Product_Name)
                    VALUES (:pid, :pname)
                    ON DUPLICATE KEY UPDATE Product_Name = VALUES(Product_Name)
                    """
                ),
                {"pid": str(r["Product_ID"]), "pname": str(r["Product_Name"])},
            )


def upsert_customer_dim(engine: Engine, df: pd.DataFrame) -> None:
    """Customer grain: one row per (CustomerID, Country) as required by schema."""
    sub = df[["CustomerID_str", "Country"]].copy()
    sub = sub[sub["CustomerID_str"] != ""]
    sub = sub.drop_duplicates(subset=["CustomerID_str", "Country"])
    with engine.begin() as conn:
        for _, r in sub.iterrows():
            conn.execute(
                text(
                    """
                    INSERT INTO Customer_Dim (Customer_ID, Country)
                    VALUES (:cid, :ctry)
                    ON DUPLICATE KEY UPDATE Country = VALUES(Country)
                    """
                ),
                {"cid": str(r["CustomerID_str"]), "ctry": str(r["Country"])},
            )


def insert_sales_fact(engine: Engine, df: pd.DataFrame, tmap: pd.DataFrame) -> int:
    """Join cleaned rows to Time_ID and insert fact rows."""
    x = df.copy()
    x["day"] = pd.to_datetime(x["InvoiceDate"]).dt.normalize()
    tmap = tmap.copy()
    tmap = tmap.rename(columns={"Date": "day"})
    x = x.merge(tmap, on="day", how="left", validate="m:1")

    miss = x["Time_ID"].isna().sum()
    if miss:
        logger.warning("Dropping %s rows with unresolved Time_ID.", int(miss))
        x = x.loc[x["Time_ID"].notna()].copy()

    fact = pd.DataFrame(
        {
            "Product_ID": x["StockCode"].astype(str),
            "Customer_ID": x["CustomerID_str"].astype(str),
            "Time_ID": x["Time_ID"].astype(int),
            "Quantity": x["Quantity"].astype(int),
            "UnitPrice": x["UnitPrice"].astype(float),
            "TotalAmount": x["TotalAmount"].astype(float),
        }
    )

    # Drop lines with empty customer id (should not happen after cleaning dropna)
    fact = fact[fact["Customer_ID"] != ""]

    chunk = 10_000
    rows = len(fact)
    # Bulk append using SQLAlchemy engine (pandas handles batching).
    fact.to_sql(
        "Sales_Fact",
        engine,
        if_exists="append",
        index=False,
        chunksize=chunk,
        method="multi",
    )
    return int(rows)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ETL cleaned CSV -> MySQL star schema.")
    p.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Cleaned CSV path (default: data/cleaned_retail_data.csv).",
    )
    p.add_argument(
        "--mysql-url",
        type=str,
        required=True,
        help="SQLAlchemy URL, e.g. mysql+pymysql://user:pass@127.0.0.1:3306/retail_dw",
    )
    p.add_argument(
        "--schema-file",
        type=Path,
        default=None,
        help="Path to schema.sql (default: database/schema.sql).",
    )
    p.add_argument("--init", action="store_true", help="Create tables using schema.sql.")
    p.add_argument(
        "--reset",
        action="store_true",
        help="Truncate tables before load (recommended for repeat runs).",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    root, data_dir = project_paths()
    csv_path = args.csv or (data_dir / "cleaned_retail_data.csv")
    schema_path = args.schema_file or (root / "database" / "schema.sql")

    try:
        engine = create_engine(args.mysql_url)

        if args.init:
            run_schema_sql(engine, schema_path)
        elif not tables_exist(engine):
            logger.error("Tables missing. Run with --init or import database/schema.sql manually.")
            return 1

        df = load_cleaned_csv(csv_path)
        logger.info("Loaded cleaned CSV: %s rows.", f"{len(df):,}")

        if args.reset:
            truncate_all(engine)

        tmap = upsert_time_dim(engine, df)
        upsert_product_dim(engine, df)
        upsert_customer_dim(engine, df)

        n = insert_sales_fact(engine, df, tmap)

        print("\n>>> ETL SUCCESS")
        print(f">>> Inserted (or refreshed) dimensions and loaded {n:,} fact rows into Sales_Fact.\n")
        return 0

    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    except OSError as exc:
        logger.error("Database I/O error: %s", exc)
        return 1
    except Exception:
        logger.exception("ETL failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
