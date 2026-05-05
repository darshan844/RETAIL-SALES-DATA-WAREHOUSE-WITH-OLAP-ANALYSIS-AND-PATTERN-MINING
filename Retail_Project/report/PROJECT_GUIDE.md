# Retail Sales Data Warehouse — Project Guide

This document explains how to run the end-to-end pipeline, what to install, how to configure MySQL, and what outputs to expect.

---

## Folder structure (Step 1)

| Folder | Purpose |
|--------|---------|
| `data/` | Raw CSV (e.g., `Online_Retail.csv`) and generated `cleaned_retail_data.csv`. |
| `scripts/` | Python programs: cleaning, ETL, mining, visualization, evaluation. |
| `database/` | `schema.sql` (DDL) and `olap_queries.sql` (analytical SQL). |
| `results/` | Mining outputs (`association_rules.csv`, `frequent_itemsets.csv`) and `charts/`. |
| `report/` | Written report materials and this guide. |

---

## Required Python libraries

Install dependencies (prefer a **virtual environment** if you use Anaconda/conda, to avoid NumPy 2.x / `pyarrow` import errors):

```bash
cd Retail_Project
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Packages: `pandas`, `numpy`, `matplotlib`, `mlxtend`, `PyMySQL`, `SQLAlchemy`, `openpyxl` (for `fetch_dataset.py`).

### Download dataset from UCI (optional)

```bash
python scripts/fetch_dataset.py
```

Writes `data/Online_Retail.csv` from the official UCI zip.

---

## Database setup (MySQL)

1. Install MySQL Server 8+.
2. Create a database and user (example):

```sql
CREATE DATABASE retail_dw CHARACTER SET utf8mb4;
CREATE USER 'retail_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON retail_dw.* TO 'retail_user'@'localhost';
FLUSH PRIVILEGES;
```

3. Apply the star schema (optional if you use ETL `--init`):

```bash
mysql -u retail_user -p retail_dw < database/schema.sql
```

---

## End-to-end pipeline (optional)

Runs cleaning, ETL, OLAP queries, Apriori mining, visualization, and evaluation in order:

```bash
python scripts/run_pipeline.py --mysql-url mysql+pymysql://retail_user:your_password@127.0.0.1:3306/retail_dw
```

- **`--olap-save-csv`** — also writes `results/olap/query_01.csv`, …
- **`--etl-no-init`** — skip DDL if tables already exist
- **`--etl-no-reset`** — do not truncate before load (not recommended)
- **`--steps clean,mine,viz`** — run only listed steps (omit `etl`/`olap` if no DB)

## How to run each script

Run commands from the `Retail_Project` folder unless noted.

### Step 2 — Data cleaning

Place the raw dataset as `data/Online_Retail.csv`, then:

```bash
python scripts/data_cleaning.py
```

**Output:** `data/cleaned_retail_data.csv`  
**What it does:** removes bad rows, parses dates, computes `TotalAmount`.

### Step 4 — Load warehouse (ETL)

```bash
python scripts/load_data_to_warehouse.py --mysql-url mysql+pymysql://retail_user:your_password@127.0.0.1:3306/retail_dw --init --reset
```

**Output:** populated `Time_Dim`, `Product_Dim`, `Customer_Dim`, `Sales_Fact`.  
**Notes:** `--init` creates tables from `database/schema.sql`. `--reset` truncates tables before reload (recommended for repeat runs).

### Step 5 — OLAP SQL

Execute queries in MySQL Workbench or CLI:

```bash
mysql -u retail_user -p retail_dw < database/olap_queries.sql
```

Or run the same queries from Python (prints tables; optional CSV export):

```bash
python scripts/run_olap_queries.py --mysql-url mysql+pymysql://retail_user:your_password@127.0.0.1:3306/retail_dw
python scripts/run_olap_queries.py --mysql-url mysql+pymysql://retail_user:your_password@127.0.0.1:3306/retail_dw --save-csv
```

With `--save-csv`, results are written under `results/olap/query_01.csv`, etc.

### Step 6 — Pattern mining (Apriori)

```bash
python scripts/pattern_mining.py
```

**Outputs:** `results/frequent_itemsets.csv`, `results/association_rules.csv`

Tune thresholds if needed:

```bash
python scripts/pattern_mining.py --min-support 0.01 --min-confidence 0.3
```

**FP-Growth (alternative):** same outputs with a `fpgrowth_` filename prefix for comparison in your report:

```bash
python scripts/pattern_mining.py --algorithm fpgrowth
python scripts/evaluation_metrics.py --algorithm fpgrowth
```

### Step 7 — Visualization

```bash
python scripts/visualization.py
```

**Outputs:** PNG files in `results/charts/`

### Step 8 — Evaluation metrics summary

```bash
python scripts/evaluation_metrics.py
```

**Output:** printed summary statistics (counts and averages).

---

## Expected outputs (checklist)

- `data/cleaned_retail_data.csv`
- MySQL tables populated (`Sales_Fact` row count matches successful ETL log)
- Optional: query results from `database/olap_queries.sql`
- `results/frequent_itemsets.csv`, `results/association_rules.csv`
- `results/charts/*.png`

---

## Troubleshooting (short)

- **Empty rules / no itemsets:** lower `--min-support` and/or `--min-confidence`.
- **ETL connection errors:** verify MySQL is running, credentials, and `mysql+pymysql://...` URL.
- **FK errors on load:** run with `--reset` after `--init` to ensure a clean load order.
