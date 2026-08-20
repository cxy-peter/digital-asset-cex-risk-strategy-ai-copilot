from __future__ import annotations

from pathlib import Path

import pandas as pd

from risk_copilot.fraud_journey import write_analysis_artifacts, write_focused_report


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data" / "demo"
    output_dir = root / "outputs" / "fraud_journey"
    users_path = data_dir / "users.csv"
    transactions_path = data_dir / "transactions.csv"
    users = pd.read_csv(users_path) if users_path.exists() else None
    transactions = pd.read_csv(transactions_path) if transactions_path.exists() else None
    paths = write_analysis_artifacts(output_dir=output_dir, users=users, transactions=transactions)
    paths["report"] = write_focused_report(output_dir / "FRAUD_JOURNEY_SOURCE_ALIGNED_REPORT.md", users)
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
