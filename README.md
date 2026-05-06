# Retail Sales Data Warehouse with OLAP Analysis and Pattern Mining

> An end-to-end data warehousing solution with OLAP analytics and market basket analysis for retail transaction data

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)

## 🎯 Project Overview

This project demonstrates a complete data warehousing pipeline for retail analytics:

1. **Data Cleaning** — Remove duplicates, parse dates, handle missing values
2. **Star Schema** — MySQL data warehouse with dimensional modeling
3. **OLAP Queries** — Analytical queries for business insights
4. **Pattern Mining** — Discover frequent itemsets and association rules (Apriori & FP-Growth)
5. **Visualization** — Charts and statistical analysis
6. **Evaluation** — Metrics for rule quality and itemset analysis

## 📊 Key Features

- **Multi-algorithm support** — Apriori and FP-Growth for association rule mining
- **OLAP capabilities** — 6 analytical queries for time-based, product, and customer analysis
- **Data quality** — Comprehensive cleaning pipeline with validation
- **Flexible pipeline** — Run end-to-end or execute individual steps
- **Results export** — CSV outputs for itemsets, rules, and OLAP queries
- **Visualizations** — Association rules, frequent itemsets, and trend charts

## 📁 Project Structure

```
Retail_Project/
├── README.md                          # Detailed project guide
├── requirements.txt                   # Python dependencies
├── data/                             # Raw and cleaned datasets
│   ├── Online_Retail.csv            # Source data (UCI online retail)
│   └── cleaned_retail_data.csv       # Processed data output
├── scripts/                          # Python pipeline components
│   ├── data_cleaning.py             # Data preprocessing
│   ├── fetch_dataset.py             # Download UCI dataset
│   ├── load_data_to_warehouse.py    # ETL to MySQL
│   ├── run_olap_queries.py          # Execute OLAP queries
│   ├── pattern_mining.py            # Apriori/FP-Growth mining
│   ├── evaluation_metrics.py        # Statistical analysis
│   ├── visualization.py             # Generate charts
│   └── run_pipeline.py              # Orchestrate full pipeline
├── database/                         # Database schema and queries
│   ├── schema.sql                   # Star schema DDL
│   ├── olap_queries.sql            # 6 analytical queries
│   └── schema_reset.sql            # Reset script
└── results/                         # Outputs directory
    ├── frequent_itemsets.csv
    ├── association_rules.csv
    ├── charts/                      # Generated visualizations
    └── olap/                        # OLAP query results
```

## 🚀 Quick Start

### 1. Set up Python Environment

```bash
cd Retail_Project
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 2. Prepare Dataset

**Option A:** Download from UCI (automatic)
```bash
python scripts/fetch_dataset.py
```

**Option B:** Use existing `Online_Retail.csv` (place in `data/` folder)

### 3. Run Full Pipeline

Without database (local processing only):
```bash
python scripts/run_pipeline.py --steps clean,mine,viz
```

With MySQL database:
```bash
python scripts/run_pipeline.py \
  --mysql-url mysql+pymysql://user:password@localhost:3306/retail_dw \
  --olap-save-csv
```

## 📋 Detailed Usage

### Data Cleaning
```bash
python scripts/data_cleaning.py
# Output: data/cleaned_retail_data.csv
```

### Pattern Mining

**Apriori Algorithm:**
```bash
python scripts/pattern_mining.py --algorithm apriori
python scripts/evaluation_metrics.py --algorithm apriori
```

**FP-Growth Algorithm:**
```bash
python scripts/pattern_mining.py --algorithm fpgrowth
python scripts/evaluation_metrics.py --algorithm fpgrowth
```

### OLAP Analysis

```bash
python scripts/run_olap_queries.py --mysql-url mysql+pymysql://user:password@localhost/retail_dw
```

### Generate Visualizations

```bash
python scripts/visualization.py
# Outputs: results/charts/*.png
```

## 🗄️ Database Setup (MySQL)

Create database and user:
```sql
CREATE DATABASE retail_dw CHARACTER SET utf8mb4;
CREATE USER 'retail_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON retail_dw.* TO 'retail_user'@'localhost';
FLUSH PRIVILEGES;
```

Load schema:
```bash
mysql -u retail_user -p retail_dw < database/schema.sql
```

## 📊 OLAP Queries Included

1. **Query 01** — Sales by month and region
2. **Query 02** — Top products by quantity
3. **Query 03** — Customer segmentation by spending
4. **Query 04** — Time-based trend analysis
5. **Query 05** — Product category performance
6. **Query 06** — Regional sales comparison

## 💾 Output Files

| File | Description |
|------|-------------|
| `frequent_itemsets.csv` | Itemsets found by Apriori/FP-Growth |
| `association_rules.csv` | Rules with support, confidence, lift |
| `fpgrowth_*.csv` | FP-Growth algorithm variants |
| `results/charts/*.png` | Visualizations and plots |
| `results/olap/*.csv` | OLAP query results |

## 🛠️ Dependencies

- **pandas** ≥ 2.0.0 — Data manipulation
- **numpy** ≥ 1.24.0 — Numerical computing
- **matplotlib** ≥ 3.7.0 — Visualizations
- **mlxtend** ≥ 0.22.0 — Pattern mining algorithms
- **PyMySQL** ≥ 1.1.0 — MySQL connector
- **SQLAlchemy** ≥ 2.0.0 — ORM
- **openpyxl** ≥ 3.1.0 — Excel support

## 🔧 Configuration

Key options for `run_pipeline.py`:

```
--mysql-url           Connection string for MySQL
--olap-save-csv       Export OLAP query results to CSV
--etl-no-init         Skip database initialization
--etl-no-reset        Skip table truncation before load
--steps               Comma-separated step list (clean,etl,olap,mine,viz,eval)
```

## 📈 Performance Notes

- **Apriori**: Full itemset generation; slower for large datasets
- **FP-Growth**: More efficient for high-support thresholds
- **Data cleaning**: ~1-2 seconds for 500K transactions
- **Mining**: ~5-10 seconds depending on min_support threshold
- **OLAP queries**: <1 second per query on indexed tables

## 📖 Documentation

For detailed setup instructions and troubleshooting, see:
- [`Retail_Project/README.md`](Retail_Project/README.md) — Technical README
- [`Retail_Project/report/PROJECT_GUIDE.md`](Retail_Project/report/PROJECT_GUIDE.md) — Complete project guide

## 🎓 Use Cases

This project is suitable for:
- **Educational** — Understanding data warehousing and OLAP
- **Prototyping** — Retail analytics baseline
- **Research** — Comparing pattern mining algorithms
- **Portfolio** — Demonstrating full-stack data engineering skills

## 📝 License

MIT License — See LICENSE file for details

## 👤 Author

**Darshan**  
[GitHub](https://github.com/darshan844) | [Repository](https://github.com/darshan844/RETAIL-SALES-DATA-WAREHOUSE-WITH-OLAP-ANALYSIS-AND-PATTERN-MINING)

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests

---

**Built with:** Python • MySQL • SQLAlchemy • MLxtend • Pandas
