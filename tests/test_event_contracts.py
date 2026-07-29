from __future__ import annotations

from pathlib import Path

from risk_copilot.features.registry import FeatureRegistry


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _registry() -> FeatureRegistry:
    return FeatureRegistry(
        PROJECT_ROOT / "configs/features.yaml",
        PROJECT_ROOT / "configs/events.yaml",
    )


def test_static_contracts_have_no_broken_references():
    report = _registry().validate_contract_consistency()
    assert report.valid is True
    assert report.error_count == 0
    assert report.event_count == 21
    assert report.feature_count == 120
    assert len(report.event_contract_hashes) == 21


def test_event_contract_is_versioned_and_reproducible():
    registry = _registry()
    first = registry.build_event_contract("ChainWithdraw")
    second = registry.build_event_contract("ChainWithdraw")

    assert first.contract_hash == second.contract_hash
    assert len(first.contract_hash) == 64
    assert first.contract_version.startswith("ChainWithdraw@sha256:")
    assert {feature.name for feature in first.features} == set(
        first.event.available_features
    )
