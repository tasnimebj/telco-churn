import csv
import hashlib
import io
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import pandas as pd


def read_dataset(source: Path) -> pd.DataFrame:
    # The supplied file wraps each comma-separated record in one quoted field.
    with source.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))

    if not rows or any(len(row) != 1 for row in rows):
        raise ValueError("Expected one outer CSV field per record.")

    decoded = "\n".join(row[0] for row in rows)
    return pd.read_csv(io.StringIO(decoded))


def inspect_dataset(source: Path) -> dict:
    df = read_dataset(source)

    missing = df.isna().sum()
    blank = df.apply(
        lambda column: (
            column.astype("string")
            .str.strip()
            .eq("")
            .fillna(False)
            .sum()
        )
    )

    target_counts = df["Churn"].value_counts(dropna=False)
    target_proportions = df["Churn"].value_counts(
        normalize=True, dropna=False
    )

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": source.as_posix(),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "reading_method": "Decode outer CSV field, then parse inner CSV",
        },
        "environment": {
            "python": sys.version,
            "pandas": version("pandas"),
            "platform": platform.platform(),
        },
        "dimensions": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
        },
        "field_types": df.dtypes.astype(str).to_dict(),
        "target_counts": {
            str(label): int(count)
            for label, count in target_counts.items()
        },
        "target_proportions": {
            str(label): float(proportion)
            for label, proportion in target_proportions.items()
        },
        "duplicate_customer_id_count": int(
            df["customerID"].duplicated().sum()
        ),
        "missing_values": {
            column: int(count) for column, count in missing.items()
        },
        "empty_or_whitespace_values": {
            column: int(count) for column, count in blank.items()
        },
    }


def main() -> None:
    source = Path("data/raw/datasets.csv")
    output = Path("reports/data_overview.json")

    report = inspect_dataset(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(f"Report saved to {output}")
    print(json.dumps(report["dimensions"], indent=2))


if __name__ == "__main__":
    main()