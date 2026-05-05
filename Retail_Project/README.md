# Retail Sales Data Warehouse — MS Project

Proof-of-concept pipeline: **clean → MySQL star schema → OLAP SQL → Apriori/FP-Growth → charts → evaluation**.

## Quick start

1. **Python environment (recommended)**

   Use a **virtual environment** so Anaconda/global packages do not break NumPy/pandas (e.g. `numpy 2.x` vs `pyarrow` conflicts):

   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install** (if not using venv)

   ```bash
   pip install -r requirements.txt
   ```

3. **Dataset** — copy `Online_Retail.csv` into `data/`, or download and convert from UCI:

   ```bash
   python scripts/fetch_dataset.py
   ```

4. **Create** MySQL database `retail_dw` and a user with access (see `report/PROJECT_GUIDE.md`). Skip if you only run cleaning/mining/charts locally.

5. **Run everything** (replace the URL with yours):

   ```bash
   python scripts/run_pipeline.py --mysql-url mysql+pymysql://USER:PASS@127.0.0.1:3306/retail_dw
   ```

6. **Or run steps manually** — see `report/PROJECT_GUIDE.md` for full commands.

**Note:** Cleaning, mining, charts, and evaluation run **without MySQL**. Only ETL + OLAP SQL need a database.

## Contents

| Path | Role |
|------|------|
| `scripts/data_cleaning.py` | Clean CSV → `data/cleaned_retail_data.csv` |
| `scripts/load_data_to_warehouse.py` | ETL into MySQL |
| `scripts/run_olap_queries.py` | OLAP SQL from Python |
| `scripts/pattern_mining.py` | Apriori or FP-Growth + rules |
| `scripts/visualization.py` | Charts → `results/charts/` |
| `scripts/evaluation_metrics.py` | Rule/itemset statistics |
| `scripts/run_pipeline.py` | Ordered end-to-end run |
| `scripts/fetch_dataset.py` | Download UCI zip → `data/Online_Retail.csv` |
| `database/schema.sql` | Star schema DDL |
| `database/olap_queries.sql` | Analytical queries |

**Documentation:** `report/PROJECT_GUIDE.md`

## FP-Growth comparison

```bash
python scripts/pattern_mining.py --algorithm fpgrowth
python scripts/evaluation_metrics.py --algorithm fpgrowth
```

Outputs `fpgrowth_frequent_itemsets.csv` and `fpgrowth_association_rules.csv`.

## Run instructions (final submission)

Run from the `Retail_Project` folder.

1. Create and activate venv, then install dependencies:

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Make sure dataset exists:

```bash
python scripts/fetch_dataset.py
```

Or place `Online_Retail.csv` manually in `data/`.

3. Create MySQL database/user (see `report/PROJECT_GUIDE.md`), then run full pipeline:

```bash
python scripts/run_pipeline.py --mysql-url mysql+pymysql://USER:PASS@127.0.0.1:3306/retail_dw --olap-save-csv
```

4. Expected outputs after successful run:

- `data/cleaned_retail_data.csv`
- `results/frequent_itemsets.csv`
- `results/association_rules.csv`
- `results/fpgrowth_frequent_itemsets.csv` (optional FP-Growth comparison)
- `results/fpgrowth_association_rules.csv` (optional FP-Growth comparison)
- `results/charts/*.png`
- `results/olap/query_01.csv` to `results/olap/query_06.csv`

## Final submission checklist

Include:

- `scripts/`
- `database/`
- `report/`
- `README.md`
- `requirements.txt`
- `data/.gitkeep` (and required dataset/results files only if your instructor asks)

Exclude:

- `.venv/`
- `__pycache__/`, `*.pyc`
- temporary files (`*.tmp`, `*.temp`)
- local logs (`*.log`)
- IDE/system files (`.idea/`, `.vscode/`, `.DS_Store`, `Thumbs.db`)

Note: if your instructor requires generated outputs, include only the needed files from `data/` and `results/` (not virtual environments or caches).
