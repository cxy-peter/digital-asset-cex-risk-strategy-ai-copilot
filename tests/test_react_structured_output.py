from __future__ import annotations

from risk_copilot.react_app import _parse_reviewer_bundle


def test_reviewer_json_is_validated_into_typed_bundle():
    text = """
    {
      "summary": "Revise before approval.",
      "findings": [
        {
          "category": "evaluation",
          "severity": "high",
          "statement": "Threshold must be chosen on development data.",
          "evidence_refs": ["model_analysis.threshold_selection_partition"]
        }
      ],
      "risks": ["selection leakage"],
      "revisions": ["freeze threshold before OOT"],
      "acceptance_tests": ["flipping OOT labels does not change threshold"],
      "evidence_refs": ["model_analysis"]
    }
    """

    bundle = _parse_reviewer_bundle(
        "feature_model_reviewer",
        text,
        attempts=1,
        latency_ms=12.0,
    )

    assert bundle.status == "succeeded"
    assert bundle.findings[0].severity == "high"
    assert bundle.attempts == 1
    assert bundle.raw_text is None


def test_invalid_reviewer_output_degrades_without_losing_raw_evidence():
    bundle = _parse_reviewer_bundle(
        "governance_operations_reviewer",
        "free-form Markdown instead of JSON",
        attempts=2,
        latency_ms=25.0,
    )

    assert bundle.status == "degraded"
    assert bundle.error is not None
    assert bundle.raw_text == "free-form Markdown instead of JSON"
    assert bundle.acceptance_tests
