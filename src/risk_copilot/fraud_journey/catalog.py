from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import product
from typing import Iterable


class CoverageStatus(str, Enum):
    EXACT = "EXACT"
    APPROXIMATE = "APPROXIMATE"
    DERIVABLE = "DERIVABLE"
    MISSING = "MISSING"
    LINEAGE_RISK = "LINEAGE_RISK"


@dataclass(frozen=True)
class FeatureMapping:
    source_feature: str
    github_feature: str | None
    status: CoverageStatus
    source_role: str
    note: str


@dataclass(frozen=True)
class AnalysisStep:
    order: int
    stage: str
    question: str
    source_method: str
    output: str
    gate: str


COHORT_DEFINITIONS: tuple[dict[str, str], ...] = (
    {
        "cohort": "excluded_accounts",
        "definition": "Internal, market-maker, test, institutional and other non-retail accounts are removed before analysis.",
        "warning": "The current synthetic users table does not expose all source account-role flags.",
    },
    {
        "cohort": "silent_users",
        "definition": "No deposit, withdrawal or trading behavior; excluded from the feature-effectiveness population.",
        "warning": "Silent does not mean low-risk in general; it means there is no behavioral exposure for this journey analysis.",
    },
    {
        "cohort": "curated_white",
        "definition": "Users in the curated white-sample list after account-role exclusions.",
        "warning": "A generic label=0 population is not equivalent to the source white sample.",
    },
    {
        "cohort": "curated_black",
        "definition": "Official Fraud users plus previously cleared/removed Fraud users, after account-role exclusions.",
        "warning": "Black-sample source and observation date must be retained; unlabelled is not automatically clean.",
    },
    {
        "cohort": "unlabelled_population",
        "definition": "Eligible retail users absent from both curated black and white lists.",
        "warning": "Used for distribution and discovery, not as a clean negative label by default.",
    },
    {
        "cohort": "target_try_trading_segment",
        "definition": "Users touching TRY-USDT, TRY-TRX or TRY-BTC pathways, with multi-pair activity retained as a separate flag.",
        "warning": "The source later found that many Fraud users also traded multiple pairs, so pair filtering cannot be the only inclusion rule.",
    },
)


SOURCE_ANALYSIS_STEPS: tuple[AnalysisStep, ...] = (
    AnalysisStep(
        1,
        "objective_and_baseline",
        "What business gap is the Q4 Fraud project trying to close?",
        "Use Q3 as baseline; compare existing online strategy coverage and target additional black-sample recall through online and offline controls.",
        "Objective, action boundary, review capacity and baseline confusion matrix.",
        "No model work until the event, population, action and metric are explicit.",
    ),
    AnalysisStep(
        2,
        "label_and_population_contract",
        "Who is black, white, unlabelled or excluded?",
        "Add previously Fraud-cleared users; remove internal/market-maker/test/institutional accounts; exclude silent users; preserve label source and maturity.",
        "Versioned user-label table with source, observed_at and eligibility flags.",
        "Do not equate every label=0 row with the curated white sample.",
    ),
    AnalysisStep(
        3,
        "trading_pair_and_behavioral_scope",
        "Which trading pathways are representative enough for analysis?",
        "Measure pair coverage, transaction count and amount; isolate TRY-USDT/TRX/BTC while retaining a multi-pair indicator and small-altcoin segment.",
        "Pair-level cohort table and coverage report.",
        "A pair is a segment variable, not a universal Fraud definition.",
    ),
    AnalysisStep(
        4,
        "bank_data_quality_and_features",
        "Can bank identity and bank-risk signals be calculated reliably?",
        "Audit cardNumber, bankCode, bankUserName/bankUserBame and bankName; reconcile masked cards; calculate unique withdrawal cards and bank Fraud ratios.",
        "Bank data-quality report and bank feature table.",
        "Field aliases and missingness are resolved before model use.",
    ),
    AnalysisStep(
        5,
        "existing_feature_family_review",
        "Which existing numeric, ratio and count features are actually discriminative?",
        "Compare robust distributions for amount/time, closed-loop ratios, rapid cash-out and event counts; use per-user statistics to avoid whale domination.",
        "Feature-family findings and candidate list.",
        "No single behavior is treated as Fraud without corroborating evidence.",
    ),
    AnalysisStep(
        6,
        "single_feature_effectiveness",
        "Does each candidate have stable and interpretable signal?",
        "Use binned bad-rate curves, AUC, KS, IV/WOE, Lift at operating depth, support and direction; merge tiny categories.",
        "Feature evidence cards.",
        "Thresholds in the source report are heuristics, not universal production standards.",
    ),
    AnalysisStep(
        7,
        "black_user_full_journey",
        "What mechanism is visible from registration through withdrawal?",
        "Inspect 5-10 or a small audited set of black users across registration, KYC, funding, trading, withdrawal, active time, IP/device/address and front-end operations.",
        "Case-level journey timelines and testable hypotheses.",
        "Small-case findings must be validated against white and unlabelled cohorts.",
    ),
    AnalysisStep(
        8,
        "behavior_sequence_analysis",
        "Are there repeatable event-order or timing patterns beyond snapshot counters?",
        "Use the last four months and at most 200 events for users with at least 10 events; retain user-originated business events and exclude system-derived events.",
        "Sequence statistics, n-grams/embeddings candidates and session metrics.",
        "Do not use raw sub-second gaps until parent-child/system events are removed.",
    ),
    AnalysisStep(
        9,
        "onchain_and_risk_graph",
        "Do black users share destinations, risky services or strong identity relations?",
        "Classify destination type and chain labels; compare exchange/private/unknown destinations; expand strong one-hop and controlled two-hop graph relations with super-node suppression.",
        "Address intelligence and explainable graph paths.",
        "The exchange-vs-private preference in the source was a hypothesis to test, not a confirmed conclusion.",
    ),
    AnalysisStep(
        10,
        "tree_feature_interactions",
        "Which interpretable feature combinations create high-risk branches?",
        "Train constrained trees; inspect minimum leaf size, risk order, cross-period stability and false positives; convert only stable paths into candidate rules.",
        "Candidate rule paths with support and risk rate.",
        "A deep tree is an exploration tool, not an online strategy by itself.",
    ),
    AnalysisStep(
        11,
        "boosting_model_comparison",
        "Can nonlinear ranking improve precision/recall over existing strategy?",
        "Compare sampling ratios 1:3, 1:4, 1:5 and no undersampling, depths 3-6 and probability thresholds 0.5-0.9; choose on Development and report natural-distribution OOT.",
        "XGBoost/optional LightGBM benchmark, calibrated scores and error analysis.",
        "1:4 is one tested ratio, not a fixed source rule; undersampling must not determine reported probability without calibration.",
    ),
    AnalysisStep(
        12,
        "strategy_translation_and_lifecycle",
        "How does analysis become online/offline controls?",
        "Translate evidence into Event + Population + Window + Threshold + Exclusion + Action; compare with existing strategy, run 1:1 simulation, second review and effectiveness monitoring.",
        "Offline list/rule candidates, online score strategy and lifecycle ticket.",
        "High-impact actions remain human-controlled and must have rollback/monitoring.",
    ),
)


BUSINESS_EVENT_CODES: tuple[str, ...] = (
    "ChainOnRecharge",
    "FiatDeposit",
    "FiatFithdrawal",
    "CoinTrGoogleCode",
    "UserKycStart",
    "KYCVerify",
    "UserKyc",
    "CashBalanceBuyCoin",
    "CashBalanceSellCoin",
    "WalletWithdraw",
    "ChainOnWithdraw",
    "UserRegister",
    "UserLogin",
    "CointrSpot",
    "InternalTransfer",
    "CoinTrFundCode",
    "CoinTrConvert",
    "CoinTrEquipmentManagement",
    "CoinTrOnChainAddressManagement",
    "UserPasswordModification",
    "CoinTrForgettingSecurityItem",
    "CoinTrUserAccountCancellation",
    "travelRuleExemption",
    "CoinTrEmailUpdate",
    "UserThirdBindAccount",
    "CoinTrUpdatePhoneNumber",
    "CoinTrAPISet",
    "ApiKeyV",
    "CoinTrEventRegistration",
    "unexemptedWithdraw",
    "CoinTrActivitySingle",
    "CoinTrActivitySingleRealTime",
    # Synthetic demo aliases.
    "FIAT_DEPOSIT",
    "FIAT_WITHDRAW",
    "CONVERT",
    "SPOT_TRADE",
    "CHAIN_DEPOSIT",
    "CHAIN_WITHDRAW",
    "INTERNAL_TRANSFER",
)


SYSTEM_EVENT_CODES: tuple[str, ...] = (
    "FiatDepositPostProcess",
    "FiatWithdrawalPostProcess",
    "BroadcastMessage",
    "BatchCampaignRequest",
    "ReconciliationCheck",
    "AdminWithdrawReport",
    "BankStatementBackend",
    "AirdropRewardDistribution",
    "CustodyDeposit",
    "CustodyWithdraw",
    "InternalFeeAccountTransfer",
    "CashBalanceBuyCoinCheck",
    "CashBalanceSellCoinCheck",
    "FundingGoogleCodeValidation",
)


MODEL_GRID: dict[str, tuple[float | int | None, ...]] = {
    "negative_to_positive_ratio": (None, 3, 4, 5),
    "max_depth": (3, 4, 5, 6),
    "probability_threshold": (0.5, 0.6, 0.7, 0.8, 0.9),
}


def model_grid_records() -> list[dict[str, float | int | None]]:
    return [
        {
            "negative_to_positive_ratio": ratio,
            "max_depth": depth,
            "probability_threshold": threshold,
        }
        for ratio, depth, threshold in product(
            MODEL_GRID["negative_to_positive_ratio"],
            MODEL_GRID["max_depth"],
            MODEL_GRID["probability_threshold"],
        )
    ]


FEATURE_MAPPINGS: tuple[FeatureMapping, ...] = (
    FeatureMapping("registration_device_side", "registration_channel", CoverageStatus.EXACT, "registration", "Android/iOS/Web/H5 is represented."),
    FeatureMapping("registration_source", "registration_channel", CoverageStatus.APPROXIMATE, "registration", "Channel exists, but source categories such as organic/ads are not separately modeled."),
    FeatureMapping("no_inviter_flag", None, CoverageStatus.MISSING, "registration", "The demo has inviter risk/cluster signals but no explicit inviter-id or no-inviter flag."),
    FeatureMapping("kyc_l1_only_flag", "kyc_level", CoverageStatus.EXACT, "kyc", "L1/L2 is represented."),
    FeatureMapping("kyc_duration_hours", "kyc_duration_minutes", CoverageStatus.DERIVABLE, "kyc", "Convert minutes to hours."),
    FeatureMapping("first_fiat_in_to_kyc_hours", "minutes_kyc_to_first_fiat_deposit", CoverageStatus.DERIVABLE, "journey_time", "Convert minutes to hours."),
    FeatureMapping("first_chain_out_5min_cnt", "chain_out_5min_count_30d", CoverageStatus.APPROXIMATE, "journey_time", "The demo has a 30-day fast-chain-out counter, not the exact source first-event definition."),
    FeatureMapping("fiat_in_amt", "fiat_deposit_amount_24h", CoverageStatus.APPROXIMATE, "fund_flow", "Window differs from the source aggregate table."),
    FeatureMapping("fiat_out_amt", "fiat_withdraw_amount_24h", CoverageStatus.APPROXIMATE, "fund_flow", "Window differs from the source aggregate table."),
    FeatureMapping("chain_in_amt", "chain_in_amount_24h", CoverageStatus.APPROXIMATE, "fund_flow", "Window differs from the source aggregate table."),
    FeatureMapping("chain_out_amt", "chain_out_amount_24h", CoverageStatus.APPROXIMATE, "fund_flow", "Window differs from the source aggregate table."),
    FeatureMapping("spot_trade_amt", "spot_trade_amount_24h", CoverageStatus.APPROXIMATE, "trading", "The demo does not split buy and sell amount."),
    FeatureMapping("spot_trade_count", "spot_trade_count_24h", CoverageStatus.APPROXIMATE, "trading", "The source has several buy/sell/group counters; the demo has one total counter."),
    FeatureMapping("trade_pair_count", "trade_pair_count_30d", CoverageStatus.EXACT, "trading", "Number of pairs exists."),
    FeatureMapping("USDTTRY_TRXTRY_BTCTRY_flags", None, CoverageStatus.MISSING, "trading", "The event demo has assets but no source-aligned spot symbol/pair field."),
    FeatureMapping("small_altcoin_under_1000u", None, CoverageStatus.MISSING, "trading", "Requires symbol, side and per-order amount."),
    FeatureMapping("fund_flow_cv", "fiat_deposit_amount_24h,chain_out_amount_24h,spot_trade_amount_24h", CoverageStatus.DERIVABLE, "fund_flow", "Derive stdev/mean across aligned amounts; current windows are only approximate."),
    FeatureMapping("fund_flow_range_ratio", "fiat_deposit_amount_24h,chain_out_amount_24h,spot_trade_amount_24h", CoverageStatus.DERIVABLE, "fund_flow", "Derive (max-min)/mean across aligned amounts."),
    FeatureMapping("fiat_in_crypto_out_ratio", "fiat_in_crypto_out_ratio", CoverageStatus.EXACT, "fund_flow", "Closed-loop ratio exists."),
    FeatureMapping("fund_stay_time", "fund_stay_minutes_median", CoverageStatus.EXACT, "fund_flow", "Median fund-stay time exists."),
    FeatureMapping("single_fiat_in_more_10000u_cnt", "single_fiat_deposit_over_10000_cnt_30d", CoverageStatus.EXACT, "fund_flow", "Count exists with a 30-day window."),
    FeatureMapping("single_fiat_in_less_3000u_cnt", "small_fiat_deposit_count_24h", CoverageStatus.APPROXIMATE, "fund_flow", "The demo has a small-deposit counter but not the exact source threshold/window contract."),
    FeatureMapping("avg_bank_fraud_ratio", "bank_fraud_ratio_max", CoverageStatus.APPROXIMATE, "bank", "Maximum bank Fraud ratio exists; source average ratio is missing."),
    FeatureMapping("withdrawal_unique_bankcards", "unique_withdraw_bankcards_30d", CoverageStatus.EXACT, "bank", "Unique withdrawal cards exists."),
    FeatureMapping("deposit_unique_bankcards", "unique_deposit_bankcards_30d", CoverageStatus.EXACT, "bank", "Unique deposit cards exists."),
    FeatureMapping("bank_user_name_card_reconciliation", None, CoverageStatus.MISSING, "bank", "Raw masked card, bank code and user-name fields are not in the public demo."),
    FeatureMapping("deposit_coin_count", None, CoverageStatus.MISSING, "fund_flow", "The demo has aggregate assets/events but no user-level deposit coin count."),
    FeatureMapping("withdraw_coin_count", None, CoverageStatus.MISSING, "fund_flow", "The demo has aggregate assets/events but no user-level withdrawal coin count."),
    FeatureMapping("withdraw_address_count", "address_similarity_cluster_size", CoverageStatus.APPROXIMATE, "address", "Cluster size is not the same as unique withdrawal destination count."),
    FeatureMapping("withdraw_ip_count", "login_ip_count_24h", CoverageStatus.APPROXIMATE, "device_ip", "Login-IP count is not withdrawal-IP count."),
    FeatureMapping("new_device_flag", "new_device_flag", CoverageStatus.EXACT, "device_ip", "Exists."),
    FeatureMapping("new_withdraw_address_flag", "new_withdraw_address_flag", CoverageStatus.EXACT, "address", "Exists."),
    FeatureMapping("new_ip_flag", None, CoverageStatus.MISSING, "device_ip", "Proxy and IP counts exist, but no explicit first-seen IP flag."),
    FeatureMapping("api_use_flag_or_count", "api_activity_ratio_30d,api_permission_risk", CoverageStatus.APPROXIMATE, "behavior", "Ratio/risk exists, exact event count does not."),
    FeatureMapping("night_activity_ratio", "night_activity_ratio_30d", CoverageStatus.EXACT, "behavior", "Exists, although the source found it could reduce model quality."),
    FeatureMapping("behavior_event_count", "behavior_event_count_30d", CoverageStatus.EXACT, "behavior", "Exists."),
    FeatureMapping("behavior_event_diversity", "behavior_event_diversity_30d", CoverageStatus.EXACT, "behavior", "Exists."),
    FeatureMapping("behavior_success_ratio", "behavior_success_ratio_30d", CoverageStatus.EXACT, "behavior", "Exists."),
    FeatureMapping("strategy_hit_frequency", "strategy_hit_count_30d,strategy_avoidance_ratio_30d", CoverageStatus.LINEAGE_RISK, "behavior", "The public generator must not derive this feature from the target label or downstream disposition."),
    FeatureMapping("one_hop_fraud_relations", "strong_relation_fraud_1hop_count", CoverageStatus.EXACT, "graph", "Created after graph enrichment."),
    FeatureMapping("fraud_graph_score", "fraud_graph_score", CoverageStatus.EXACT, "graph", "Exists after graph enrichment."),
    FeatureMapping("exchange_private_unknown_destination", None, CoverageStatus.MISSING, "onchain", "Destination entity exists, but address-type classification is absent."),
    FeatureMapping("chainalysis_service_exposure", "high_risk_chain_exposure,mixer_exposure,gambling_exposure,sanctioned_address_flag", CoverageStatus.EXACT, "onchain", "Sanitized risk-service exposure fields exist."),
    FeatureMapping("account_role_exclusion", None, CoverageStatus.MISSING, "population", "Internal/market-maker/test/institutional flags are not exposed in the current users demo."),
    FeatureMapping("official_vs_cleared_fraud_source", None, CoverageStatus.MISSING, "label", "The current demo has one fraud_label without source provenance."),
    FeatureMapping("label_observed_at", "transactions.label_observed_at", CoverageStatus.APPROXIMATE, "label", "Delayed observation exists on transaction events, not on the user-snapshot label contract."),
)


def mappings_for_columns(columns: Iterable[str]) -> list[FeatureMapping]:
    available = set(columns)
    resolved: list[FeatureMapping] = []
    for item in FEATURE_MAPPINGS:
        if item.github_feature and item.status in {CoverageStatus.EXACT, CoverageStatus.APPROXIMATE}:
            candidates = [part.strip() for part in item.github_feature.split(",")]
            if not any(name in available for name in candidates):
                resolved.append(
                    FeatureMapping(
                        item.source_feature,
                        item.github_feature,
                        CoverageStatus.MISSING,
                        item.source_role,
                        f"Configured mapping exists, but none of {candidates} is present in the supplied table.",
                    )
                )
                continue
        resolved.append(item)
    return resolved
