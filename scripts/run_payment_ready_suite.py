from __future__ import annotations

from pathlib import Path

from risk_copilot.payment import run_payment_ready_suite


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    result = run_payment_ready_suite(project_root / "outputs" / "payment_ready_suite")
    print(result.model_dump_json(indent=2))
