import asyncio
from pathlib import Path

from risk_copilot.orchestrator import RiskStrategyCopilot
from risk_copilot.schemas import StrategyRequest

ROOT = Path(__file__).resolve().parents[1]


def test_strategy_smoke():
    copilot = RiskStrategyCopilot.create(ROOT)
    state = asyncio.run(copilot.run_strategy(StrategyRequest(request_id="SMOKE", query="快速法币入金后链上提币并关联Fraud设备")))
    package = state.context["strategy_package"]
    assert package.selected_metrics.sample_size > 0
    assert package.strategy_test_environment["production_connection"] is False
    assert package.strategy_test_environment["dispatch_performed"] is False
    assert package.strategy_test_environment["current_stage"] in {"simulation_execution", "independent_second_review"}
    stage_names = {item["name"] for item in package.strategy_test_environment["stages"]}
    assert "independent_second_review" in stage_names
    assert "post_launch_observation" in stage_names
    assert package.effectiveness_ticket["synthetic_demo"] is True
    assert package.cms_str_integration["external_submission_allowed"] is False
    assert package.selected_strategy.tag_level_1 != "unclassified"
    assert Path(state.context["strategy_artifacts"]["html"]).exists()
    assert Path(state.context["strategy_artifacts"]["strategy_test_environment_json"]).exists()
    assert Path(state.context["strategy_artifacts"]["effectiveness_ticket_json"]).exists()
    assert Path(state.context["strategy_artifacts"]["cms_str_integration_json"]).exists()
    assert package.ai_advisory_board["decision"] in {
        "SUBMIT_FOR_INDEPENDENT_REVIEW", "REVISE", "REJECT_AS_DUPLICATE"
    }
    assert package.stability_analysis["status"] in {"STABLE", "WATCH", "UNSTABLE"}
    assert package.conflict_analysis["recommendation"] in {
        "ACCEPT_INCREMENTAL_VALUE", "REVISE_ACTION_PRECEDENCE", "REJECT_DUPLICATE"
    }
    assert Path(state.context["strategy_artifacts"]["ai_advisory_board_markdown"]).exists()
    assert Path(state.context["strategy_artifacts"]["strategy_stability_json"]).exists()
    assert Path(state.context["strategy_artifacts"]["strategy_conflict_json"]).exists()
