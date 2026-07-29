from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from ..config import load_yaml
from ..features.registry import FeatureRegistry


@dataclass
class TestEnvironmentGate:
    """Fail-closed validation for AI-created strategy payloads in simulation."""

    __test__ = False

    config_path: str | Path
    registry: FeatureRegistry
    config: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        self.config = load_yaml(self.config_path)

    def assess(
        self,
        *,
        event_code: str,
        feature_names: Iterable[str],
        requested_status: str = "DRAFT",
        payload_confirmed: bool = False,
        production_connection: bool = False,
    ) -> dict[str, Any]:
        names = list(dict.fromkeys(str(item) for item in feature_names))
        blockers: list[str] = []
        if event_code not in set(self.config["event_allowlist"]):
            blockers.append(f"event_not_allowlisted:{event_code}")
        try:
            self.registry.event(event_code)
        except KeyError:
            blockers.append(f"event_not_registered:{event_code}")
        else:
            blockers.extend(
                f"feature_contract:{error}"
                for error in self.registry.validate_decision_time(names, event_code)
            )

        allowed_statuses = set(self.config["strategy_creation"]["allowed_statuses"])
        if requested_status not in allowed_statuses:
            blockers.append(f"status_not_allowed_in_test_environment:{requested_status}")
        if (
            self.config["strategy_creation"]["payload_confirmation_required"]
            and not payload_confirmed
        ):
            blockers.append("payload_confirmation_required")
        if production_connection or self.config["production_connection"]:
            blockers.append("production_connection_forbidden")

        return {
            "schema_version": self.config["schema_version"],
            "environment_id": self.config["environment_id"],
            "mode": self.config["mode"],
            "event_code": event_code,
            "registered_features": names,
            "requested_status": requested_status,
            "allowed": not blockers,
            "blockers": blockers,
            "creator_marker": self.config["strategy_creation"]["creator_marker"],
            "catalog_snapshot_cadence": self.config["catalog_snapshot_cadence"],
            "production_connection": False,
            "direct_production_release": False,
        }
