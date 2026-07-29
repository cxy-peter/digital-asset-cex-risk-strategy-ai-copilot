from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from ..config import load_yaml
from ..schemas import (
    ContractIssue,
    ContractValidationReport,
    EventContract,
    EventSpec,
    FeatureSpec,
    RiskDomain,
)


class FeatureRegistry:
    def __init__(self, features_path: str | Path, events_path: str | Path) -> None:
        self.features = [FeatureSpec.model_validate(item) for item in load_yaml(features_path)]
        self.events = [EventSpec.model_validate(item) for item in load_yaml(events_path)]
        self._features = {item.name: item for item in self.features}
        self._events = {item.code: item for item in self.events}

    def feature(self, name: str) -> FeatureSpec:
        return self._features[name]

    def event(self, code: str) -> EventSpec:
        return self._events[code]

    def build_event_contract(self, code: str) -> EventContract:
        event = self.event(code)
        features = self.for_event(code)
        issues = [
            issue
            for issue in self.validate_contract_consistency().issues
            if issue.event_code == code
        ]
        canonical = {
            "event": event.model_dump(mode="json"),
            "features": [feature.model_dump(mode="json") for feature in features],
        }
        contract_hash = hashlib.sha256(
            json.dumps(
                canonical,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return EventContract(
            contract_version=f"{code}@sha256:{contract_hash[:12]}",
            contract_hash=contract_hash,
            event=event,
            features=features,
            validation_issues=issues,
        )

    def for_event(self, code: str) -> list[FeatureSpec]:
        event = self.event(code)
        return [self._features[name] for name in event.available_features if name in self._features]

    def search(
        self,
        text: str = "",
        domain: RiskDomain | str | None = None,
        event_code: str | None = None,
        tags: Iterable[str] | None = None,
    ) -> list[FeatureSpec]:
        terms = [token.lower() for token in text.split() if token.strip()]
        required_tags = set(tags or [])
        domain_value = domain.value if isinstance(domain, RiskDomain) else domain
        event_features = set(self.event(event_code).available_features) if event_code else None
        results = []
        for spec in self.features:
            if domain_value and spec.domain.value != domain_value:
                continue
            if event_features is not None and spec.name not in event_features:
                continue
            if required_tags and not required_tags.intersection(spec.tags):
                continue
            haystack = " ".join([spec.name, spec.display_name, spec.description, " ".join(spec.tags)]).lower()
            if terms and not all(term in haystack for term in terms):
                continue
            results.append(spec)
        return results

    def validate_decision_time(self, feature_names: Iterable[str], event_code: str) -> list[str]:
        errors = []
        event = self.event(event_code)
        allowed = set(event.available_features)
        for name in feature_names:
            if name.startswith("model_score__"):
                # A deployed model score is a versioned derived feature. The model artifact and
                # serving SLA must still be registered in the engine payload and approval record.
                continue
            if name not in self._features:
                errors.append(f"unknown feature: {name}")
            elif name not in allowed:
                errors.append(f"feature {name} is not registered for event {event_code}")
            elif self._features[name].available_at != "decision_time":
                errors.append(f"feature {name} is not available at decision time")
        return errors

    def validate_contract_consistency(self) -> ContractValidationReport:
        """Validate static event/feature references and publish reviewable linkage drift.

        ``EventSpec.available_features`` expresses decision-time availability, while
        ``FeatureSpec.event_codes`` records the producing/primary events. They are not required
        to be perfectly symmetric, so directional drift is a warning rather than an error.
        """

        issues: list[ContractIssue] = []
        feature_names = [item.name for item in self.features]
        event_codes = [item.code for item in self.events]
        duplicate_features = sorted({name for name in feature_names if feature_names.count(name) > 1})
        duplicate_events = sorted({code for code in event_codes if event_codes.count(code) > 1})
        for name in duplicate_features:
            issues.append(
                ContractIssue(
                    severity="error",
                    code="DUPLICATE_FEATURE",
                    feature_name=name,
                    message=f"feature name is duplicated: {name}",
                )
            )
        for code in duplicate_events:
            issues.append(
                ContractIssue(
                    severity="error",
                    code="DUPLICATE_EVENT",
                    event_code=code,
                    message=f"event code is duplicated: {code}",
                )
            )

        for event in self.events:
            if not event.available_features:
                issues.append(
                    ContractIssue(
                        severity="error",
                        code="EMPTY_EVENT_FEATURE_SET",
                        event_code=event.code,
                        message="event contract has no available features",
                    )
                )
            if not event.allowed_actions:
                issues.append(
                    ContractIssue(
                        severity="error",
                        code="EMPTY_EVENT_ACTION_SET",
                        event_code=event.code,
                        message="event contract has no allowed actions",
                    )
                )
            for name in event.available_features:
                feature = self._features.get(name)
                if feature is None:
                    issues.append(
                        ContractIssue(
                            severity="error",
                            code="UNKNOWN_EVENT_FEATURE",
                            event_code=event.code,
                            feature_name=name,
                            message=f"event references unknown feature: {name}",
                        )
                    )
                    continue
                if feature.available_at != "decision_time":
                    issues.append(
                        ContractIssue(
                            severity="error",
                            code="FEATURE_NOT_AVAILABLE_AT_DECISION",
                            event_code=event.code,
                            feature_name=name,
                            message=(
                                f"{name} is declared available to {event.code} but "
                                f"available_at={feature.available_at}"
                            ),
                        )
                    )
                if event.code not in feature.event_codes:
                    issues.append(
                        ContractIssue(
                            severity="warning",
                            code="EVENT_NOT_IN_FEATURE_LINEAGE",
                            event_code=event.code,
                            feature_name=name,
                            message=(
                                f"{name} is decision-available for {event.code}, but the event "
                                "is not listed among the feature's primary lineage events"
                            ),
                        )
                    )

        for feature in self.features:
            if not feature.source.strip():
                issues.append(
                    ContractIssue(
                        severity="error",
                        code="MISSING_FEATURE_SOURCE",
                        feature_name=feature.name,
                        message="feature source must not be empty",
                    )
                )
            for code in feature.event_codes:
                event = self._events.get(code)
                if event is None:
                    issues.append(
                        ContractIssue(
                            severity="error",
                            code="UNKNOWN_FEATURE_EVENT",
                            event_code=code,
                            feature_name=feature.name,
                            message=f"feature references unknown event: {code}",
                        )
                    )
                elif feature.name not in event.available_features:
                    issues.append(
                        ContractIssue(
                            severity="warning",
                            code="FEATURE_NOT_DECISION_AVAILABLE_FOR_LINEAGE_EVENT",
                            event_code=code,
                            feature_name=feature.name,
                            message=(
                                f"{feature.name} lists {code} as a lineage event but is not "
                                "declared decision-available in that event contract"
                            ),
                        )
                    )

        contract_hashes: dict[str, str] = {}
        for event in self.events:
            canonical = {
                "event": event.model_dump(mode="json"),
                "features": [
                    self._features[name].model_dump(mode="json")
                    for name in event.available_features
                    if name in self._features
                ],
            }
            contract_hashes[event.code] = hashlib.sha256(
                json.dumps(
                    canonical,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
        error_count = sum(issue.severity == "error" for issue in issues)
        warning_count = sum(issue.severity == "warning" for issue in issues)
        return ContractValidationReport(
            valid=error_count == 0,
            event_count=len(self.events),
            feature_count=len(self.features),
            error_count=error_count,
            warning_count=warning_count,
            issues=issues,
            event_contract_hashes=contract_hashes,
        )
