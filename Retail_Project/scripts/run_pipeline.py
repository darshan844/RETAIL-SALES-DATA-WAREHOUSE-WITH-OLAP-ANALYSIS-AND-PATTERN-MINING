"""
End-to-end pipeline driver (optional convenience).

Runs project scripts in a sensible order for demos and reproducibility:
  clean → warehouse load → OLAP queries → pattern mining → charts → evaluation

Database steps are skipped unless --mysql-url is provided.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path


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


def run(cmd: list[str], cwd: Path) -> None:
    logger.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run retail DW + mining pipeline steps.")
    p.add_argument(
        "--mysql-url",
        type=str,
        default=None,
        help="Required for etl and olap steps, e.g. mysql+pymysql://user:pass@127.0.0.1:3306/retail_dw",
    )
    p.add_argument(
        "--steps",
        type=str,
        default="all",
        help=(
            "Comma-separated: clean,etl,olap,mine,viz,eval,all. "
            "Default: all (mine uses Apriori; FP-Growth run pattern_mining.py separately)."
        ),
    )
    p.add_argument(
        "--etl-no-init",
        action="store_true",
        help="Skip DDL on ETL (tables already exist).",
    )
    p.add_argument(
        "--etl-no-reset",
        action="store_true",
        help="Do not truncate tables before ETL load (append mode — not recommended).",
    )
    p.add_argument(
        "--olap-save-csv",
        action="store_true",
        help="Pass --save-csv to run_olap_queries.py.",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)

    root = project_root()
    py = sys.executable
    scripts = root / "scripts"

    raw = [s.strip().lower() for s in args.steps.split(",") if s.strip()]
    if "all" in raw or not raw:
        steps = ["clean", "etl", "olap", "mine", "viz", "eval"]
    else:
        steps = raw

    if ("etl" in steps or "olap" in steps) and not args.mysql_url:
        logger.error("Missing --mysql-url (required for steps: etl, olap).")
        return 1

    try:
        if "clean" in steps:
            print("\n--- Step: data cleaning ---\n")
            run([py, str(scripts / "data_cleaning.py")], cwd=root)

        if "etl" in steps:
            print("\n--- Step: ETL load ---\n")
            etl_cmd = [
                py,
                str(scripts / "load_data_to_warehouse.py"),
                "--mysql-url",
                args.mysql_url,
            ]
            if not args.etl_no_init:
                etl_cmd.append("--init")
            if not args.etl_no_reset:
                etl_cmd.append("--reset")
            run(etl_cmd, cwd=root)

        if "olap" in steps:
            print("\n--- Step: OLAP queries ---\n")
            olap_cmd = [py, str(scripts / "run_olap_queries.py"), "--mysql-url", args.mysql_url]
            if args.olap_save_csv:
                olap_cmd.append("--save-csv")
            run(olap_cmd, cwd=root)

        if "mine" in steps:
            print("\n--- Step: pattern mining (Apriori) ---\n")
            run([py, str(scripts / "pattern_mining.py")], cwd=root)

        if "viz" in steps:
            print("\n--- Step: visualization ---\n")
            run([py, str(scripts / "visualization.py")], cwd=root)

        if "eval" in steps:
            print("\n--- Step: evaluation metrics ---\n")
            run([py, str(scripts / "evaluation_metrics.py")], cwd=root)

        print("\n>>> Pipeline finished successfully.\n")
        return 0

    except subprocess.CalledProcessError as exc:
        logger.error("A step failed with exit code %s.", exc.returncode)
        return exc.returncode or 1
    except FileNotFoundError:
        logger.error("Python or a script path was not found.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
