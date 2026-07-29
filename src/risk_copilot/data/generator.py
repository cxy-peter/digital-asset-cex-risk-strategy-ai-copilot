from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class DemoDataGenerator:
    seed: int = 20260728

    def __post_init__(self) -> None:
        self.rng = np.random.default_rng(self.seed)

    def generate_users(self, n: int = 10000) -> pd.DataFrame:
        rng = self.rng
        event_date = pd.to_datetime("2026-01-01") + pd.to_timedelta(rng.integers(0, 180, n), unit="D")
        registration_channel = rng.choice(["Android", "iOS", "Web", "H5"], n, p=[0.42, 0.31, 0.21, 0.06])
        kyc_level = rng.choice(["L1", "L2"], n, p=[0.16, 0.84])

        # Latent scenario memberships create interpretable correlations rather than a purely random label.
        rapid = rng.binomial(1, 0.055, n)
        ato = rng.binomial(1, 0.025, n)
        campaign = rng.binomial(1, 0.045, n)
        aml = rng.binomial(1, 0.035, n)
        graph_ring = rng.binomial(1, 0.045, n)

        age_risk = np.clip(rng.beta(2, 6, n) + 0.18 * aml, 0, 1)
        occupation_risk = np.clip(rng.beta(1.7, 6, n) + 0.28 * aml, 0, 1)
        nationality_risk = np.clip(rng.beta(1.4, 10, n) + 0.3 * aml, 0, 1)
        address_risk = np.clip(rng.beta(1.7, 8, n) + 0.25 * aml, 0, 1)

        kyc_duration = np.maximum(1, rng.lognormal(np.log(38), 0.75, n) * (1 - 0.55 * campaign))
        first_deposit = np.maximum(2, rng.lognormal(np.log(1800), 1.1, n) * (1 - 0.75 * rapid))
        first_chain_out = np.maximum(1, rng.lognormal(np.log(1200), 1.0, n) * (1 - 0.82 * rapid) * (1 - 0.35 * ato))

        fiat_in = rng.lognormal(np.log(1500), 1.25, n) * (1 + 2.5 * rapid + 1.1 * aml)
        deposit_cnt = rng.poisson(1.2 + 3.2 * rapid + 1.2 * campaign, n)
        withdraw_cnt = rng.poisson(0.7 + 3.5 * rapid + 1.2 * ato, n)
        chain_out = fiat_in * np.clip(rng.beta(2, 4, n) + 0.63 * rapid + 0.22 * aml, 0, 1.25)
        fiat_out = fiat_in * np.clip(rng.beta(1.5, 5, n) + 0.2 * ato, 0, 1.1)
        spot_trade_amt = fiat_in * np.clip(rng.normal(1.0 + 0.05 * rapid, 0.22, n), 0, 2.5)
        trade_count = rng.poisson(5 + 2 * rapid + 8 * campaign, n)
        trade_pairs = np.maximum(1, rng.poisson(4.5 - 2.2 * rapid, n))
        closed_loop = np.clip(chain_out / np.maximum(fiat_in, 1), 0, 1.5)
        fund_stay = np.maximum(1, first_chain_out * rng.uniform(0.5, 1.5, n))

        device_users = np.maximum(1, rng.poisson(0.7 + 5.5 * campaign + 2.5 * graph_ring, n))
        ip_users = np.maximum(1, rng.poisson(1.5 + 4 * campaign, n))
        proxy = rng.binomial(1, np.clip(0.06 + 0.42 * campaign + 0.2 * ato, 0, 0.9), n)
        emulator = rng.binomial(1, np.clip(0.02 + 0.5 * campaign, 0, 0.85), n)
        new_device = rng.binomial(1, np.clip(0.08 + 0.6 * ato, 0, 0.9), n)
        failed_login = rng.poisson(0.35 + 5.2 * ato, n)
        geo_velocity = rng.gamma(1.5, 40, n) + ato * rng.gamma(4, 250, n)
        password_change = rng.binomial(1, np.clip(0.05 + 0.45 * ato, 0, 0.8), n)
        new_address = rng.binomial(1, np.clip(0.13 + 0.6 * ato + 0.2 * rapid, 0, 0.95), n)

        high_risk_chain = np.clip(rng.beta(0.9, 12, n) + 0.45 * aml, 0, 1)
        mixer = np.clip(rng.beta(0.7, 25, n) + 0.3 * aml, 0, 1)
        gambling = np.clip(rng.beta(0.8, 20, n) + 0.24 * aml, 0, 1)
        sanctioned = rng.binomial(1, np.clip(0.001 + 0.08 * aml, 0, 0.3), n)
        bank_ratio = np.clip(rng.beta(1.5, 10, n) + 0.38 * rapid, 0, 1)
        unique_deposit_cards = np.maximum(1, rng.poisson(0.6 + 2.5 * rapid, n))
        unique_withdraw_cards = np.maximum(1, rng.poisson(0.45 + 1.5 * ato + 1.2 * rapid, n))
        bank_name_mismatch = rng.binomial(1, np.clip(0.015 + 0.25 * rapid + 0.12 * aml, 0, 0.7), n)
        large_deposit_count = rng.poisson(0.05 + 0.8 * rapid + 0.35 * aml, n)
        small_deposit_count = rng.poisson(0.5 + 4 * rapid + 2 * campaign, n)
        roundness = np.clip(rng.beta(1.7, 6, n) + 0.35 * aml, 0, 1)

        internal_count = rng.poisson(0.6 + 3.2 * graph_ring + 1.3 * aml, n)
        internal_amount = rng.lognormal(np.log(350), 1.0, n) * (1 + 5 * graph_ring)
        fan_in = rng.poisson(0.8 + 6 * graph_ring, n)
        fan_out = rng.poisson(0.7 + 5 * graph_ring, n)
        counterparty_ratio = np.clip(rng.beta(0.8, 15, n) + 0.55 * graph_ring, 0, 1)

        campaign_similarity = np.clip(rng.beta(1.2, 8, n) + 0.68 * campaign, 0, 1)
        inviter_cluster = np.maximum(1, rng.poisson(1 + 10 * campaign, n))
        reward_cluster = np.maximum(1, rng.poisson(0.5 + 7 * campaign, n))
        campaign_history = rng.poisson(0.05 + 1.5 * campaign, n)

        # A reasonably noisy label with multiple risk domains represented.
        logit = (
            -5.1
            + 2.4 * rapid
            + 2.2 * ato
            + 1.6 * campaign
            + 1.9 * aml
            + 1.4 * graph_ring
            + 1.5 * (closed_loop > 0.85)
            + 1.2 * (first_chain_out < 240)
            + 1.0 * (bank_ratio > 0.35)
            + 1.4 * (high_risk_chain > 0.25)
            + 1.1 * (device_users >= 4)
            + 1.2 * (failed_login >= 5)
            + rng.normal(0, 0.65, n)
        )
        probability = 1 / (1 + np.exp(-logit))
        fraud_label = rng.binomial(1, probability)
        # Ensure a useful but realistic demo positive rate.
        if fraud_label.mean() < 0.045:
            fraud_label[np.argsort(probability)[-int(n * 0.05):]] = 1

        estimated_loss = rng.lognormal(np.log(800), 1.25, n) * (0.25 + 3.5 * fraud_label)
        risk_score_t1 = np.clip(
            0.10 + 0.30 * closed_loop + 0.24 * high_risk_chain + 0.18 * proxy + 0.20 * counterparty_ratio
            + 0.12 * occupation_risk + rng.normal(0, 0.07, n), 0, 1
        )
        declared_monthly_income = rng.lognormal(np.log(2200), 0.8, n)
        expected_monthly_volume = declared_monthly_income * rng.uniform(0.8, 4.5, n)
        observed_to_expected = (
            fiat_in + chain_out + fiat_out
        ) / np.maximum(expected_monthly_volume, 100)
        document_confidence = np.clip(
            rng.normal(0.94, 0.05, n) - 0.23 * campaign - 0.08 * aml,
            0,
            1,
        )
        face_match_score = np.clip(
            rng.normal(0.95, 0.04, n) - 0.24 * campaign,
            0,
            1,
        )
        liveness_score = np.clip(
            rng.normal(0.96, 0.035, n) - 0.28 * campaign,
            0,
            1,
        )
        identity_mismatch = rng.binomial(
            1,
            np.clip(0.006 + 0.22 * campaign + 0.08 * aml, 0, 0.7),
            n,
        )
        pep_flag = rng.binomial(1, np.clip(0.006 + 0.035 * aml, 0, 0.12), n)
        sanctions_screening_hit = rng.binomial(
            1,
            np.clip(0.0005 + 0.035 * aml, 0, 0.15),
            n,
        )
        source_of_funds_risk = np.clip(
            rng.beta(1.4, 8, n) + 0.38 * aml + 0.18 * rapid,
            0,
            1,
        )
        # Point-in-time behavior-sequence snapshots.  These fields emulate the registered
        # counters described in the internship material: event volume/diversity, API and
        # night-time activity, strategy-hit avoidance, and very-fast chain withdrawals.
        # They are generated as of ``event_date`` and therefore do not read the later
        # transaction-event demo or any future case disposition.
        behavior_event_count_30d = rng.poisson(
            22 + 30 * rapid + 14 * ato + 18 * campaign + 16 * aml,
            n,
        )
        behavior_event_diversity_30d = np.clip(
            rng.poisson(5 + 1.2 * aml + 0.8 * ato, n),
            1,
            14,
        )
        behavior_success_ratio_30d = np.clip(
            rng.beta(9, 2, n) - 0.12 * ato + 0.05 * rapid,
            0,
            1,
        )
        api_activity_ratio_30d = np.clip(
            rng.beta(1.3, 9, n) + 0.38 * ato + 0.16 * aml,
            0,
            1,
        )
        night_activity_ratio_30d = np.clip(
            rng.beta(1.8, 7, n) + 0.26 * ato + 0.18 * campaign,
            0,
            1,
        )
        strategy_avoidance_ratio_30d = np.clip(
            rng.beta(1.2, 9, n) + 0.42 * rapid + 0.28 * aml,
            0,
            1,
        )
        chain_out_5min_count_30d = rng.poisson(
            0.04 + 1.8 * rapid + 0.55 * aml,
            n,
        )

        df = pd.DataFrame({
            "user_id": [f"U{i:07d}" for i in range(n)],
            "event_date": event_date,
            "registration_channel": registration_channel,
            "kyc_level": kyc_level,
            "inviter_risk_score": np.clip(rng.beta(1.2, 10, n) + 0.55 * campaign, 0, 1),
            "kyc_country_risk": nationality_risk,
            "age_risk_score": age_risk,
            "occupation_risk_score": occupation_risk,
            "nationality_risk_score": nationality_risk,
            "address_risk_score": address_risk,
            "kyc_duration_minutes": kyc_duration,
            "minutes_kyc_to_first_fiat_deposit": first_deposit,
            "minutes_deposit_to_first_chain_out": first_chain_out,
            "fiat_deposit_amount_24h": fiat_in,
            "fiat_deposit_count_24h": deposit_cnt,
            "fiat_withdraw_amount_24h": fiat_out,
            "fiat_withdraw_count_24h": withdraw_cnt,
            "chain_in_amount_24h": rng.lognormal(np.log(450), 1.2, n) * (1 + aml),
            "chain_out_amount_24h": chain_out,
            "chain_withdraw_count_24h": withdraw_cnt + rng.poisson(0.4, n),
            "spot_trade_amount_24h": spot_trade_amt,
            "spot_trade_count_24h": trade_count,
            "trade_pair_count_30d": trade_pairs,
            "convert_amount_24h": fiat_in * np.clip(rng.beta(1.8, 4, n) + 0.35 * rapid, 0, 1.3),
            "convert_count_24h": rng.poisson(0.6 + 2.0 * rapid, n),
            "minutes_fiat_in_to_convert": np.maximum(1, rng.lognormal(np.log(480), 1.0, n) * (1 - 0.65 * rapid)),
            "minutes_convert_to_chain_out": np.maximum(1, rng.lognormal(np.log(360), 1.0, n) * (1 - 0.72 * rapid)),
            "fiat_in_crypto_out_ratio": closed_loop,
            "fund_stay_minutes_median": fund_stay,
            "unique_deposit_bankcards_30d": unique_deposit_cards,
            "unique_withdraw_bankcards_30d": unique_withdraw_cards,
            "bank_fraud_ratio_max": bank_ratio,
            "new_bankcard_flag": rng.binomial(1, np.clip(0.1 + 0.3 * rapid, 0, 0.8), n),
            "bank_name_mismatch_flag": bank_name_mismatch,
            "single_fiat_deposit_over_10000_cnt_30d": large_deposit_count,
            "small_fiat_deposit_count_24h": small_deposit_count,
            "amount_roundness_score": roundness,
            "new_device_flag": new_device,
            "device_user_count_24h": device_users,
            "device_user_count_30d": device_users + rng.poisson(1.2, n),
            "login_ip_count_24h": np.maximum(1, rng.poisson(1 + 1.5 * ato, n)),
            "ip_user_count_24h": ip_users,
            "proxy_flag": proxy,
            "emulator_flag": emulator,
            "geo_velocity_kmh": geo_velocity,
            "failed_login_count_1h": failed_login,
            "failed_login_count_24h": failed_login + rng.poisson(0.6, n),
            "recent_password_change_flag": password_change,
            "phone_change_7d_flag": rng.binomial(1, np.clip(0.02 + 0.25 * ato, 0, 0.6), n),
            "email_change_7d_flag": rng.binomial(1, np.clip(0.02 + 0.22 * ato, 0, 0.6), n),
            "new_withdraw_address_flag": new_address,
            "address_similarity_cluster_size": np.maximum(1, rng.poisson(0.5 + 4.5 * graph_ring + 1.2 * ato, n)),
            "api_permission_risk": np.clip(rng.beta(1.2, 8, n) + 0.5 * ato, 0, 1),
            "high_risk_chain_exposure": high_risk_chain,
            "sanctioned_address_flag": sanctioned,
            "mixer_exposure": mixer,
            "gambling_exposure": gambling,
            "source_hop_distance": np.maximum(1, rng.poisson(5 - 2.5 * aml, n)),
            "internal_transfer_amount_24h": internal_amount,
            "internal_transfer_count_24h": internal_count,
            "fan_in_degree_24h": fan_in,
            "fan_out_degree_24h": fan_out,
            "counterparty_fraud_ratio": counterparty_ratio,
            "wash_trade_similarity": np.clip(rng.beta(1, 10, n) + 0.4 * graph_ring, 0, 1),
            "cancel_ratio_1h": np.clip(rng.beta(2, 6, n) + 0.3 * graph_ring, 0, 1),
            "campaign_task_similarity": campaign_similarity,
            "inviter_cluster_size": inviter_cluster,
            "reward_address_cluster_size": reward_cluster,
            "campaign_history_abuse_count": campaign_history,
            "email_similarity_cluster_size": np.maximum(1, rng.poisson(0.6 + 5 * campaign, n)),
            "kyc_document_similarity_count": rng.poisson(0.02 + 1.2 * campaign, n),
            "kyc_device_user_count": np.maximum(1, rng.poisson(0.7 + 3 * campaign, n)),
            "declared_monthly_income_usdt": declared_monthly_income,
            "expected_monthly_volume_usdt": expected_monthly_volume,
            "observed_to_expected_volume_ratio": observed_to_expected,
            "document_ocr_confidence": document_confidence,
            "face_match_score": face_match_score,
            "liveness_score": liveness_score,
            "identity_field_mismatch_flag": identity_mismatch,
            "pep_flag": pep_flag,
            "sanctions_screening_hit": sanctions_screening_hit,
            "source_of_funds_risk": source_of_funds_risk,
            "behavior_event_count_30d": behavior_event_count_30d,
            "behavior_event_diversity_30d": behavior_event_diversity_30d,
            "behavior_success_ratio_30d": behavior_success_ratio_30d,
            "api_activity_ratio_30d": api_activity_ratio_30d,
            "night_activity_ratio_30d": night_activity_ratio_30d,
            "strategy_avoidance_ratio_30d": strategy_avoidance_ratio_30d,
            "chain_out_5min_count_30d": chain_out_5min_count_30d,
            "register_ip_country_risk": np.clip(rng.beta(1.2, 8, n) + 0.18 * campaign, 0, 1),
            "risk_score_t1": risk_score_t1,
            "risk_level_change_30d": rng.poisson(0.15 + 1.4 * fraud_label, n),
            "strategy_hit_count_30d": rng.poisson(0.3 + 3.5 * fraud_label, n),
            "rfi_count_180d": rng.poisson(0.05 + 0.8 * fraud_label, n),
            "restriction_count_180d": rng.poisson(0.03 + 0.55 * fraud_label, n),
            "fraud_label": fraud_label,
            "estimated_loss_amount": estimated_loss,
            "latent_rapid_cashout": rapid,
            "latent_ato": ato,
            "latent_campaign": campaign,
            "latent_aml": aml,
            "latent_graph_ring": graph_ring,
        })
        return df.sort_values("event_date").reset_index(drop=True)

    def generate_graph_edges(self, users: pd.DataFrame) -> pd.DataFrame:
        rng = self.rng
        n = len(users)
        fraud_count = int(users["fraud_label"].sum())
        edges: list[dict] = []

        relation_config = {
            "device": (max(100, int(n * 0.63)), 1.0),
            "email": (max(100, int(n * 0.91)), 0.85),
            "mobile": (max(100, int(n * 0.94)), 0.95),
            "kyc_id": (max(100, int(n * 0.975)), 1.0),
            "withdraw_address": (max(100, int(n * 0.78)), 1.0),
            "ip": (max(100, int(n * 0.34)), 0.25),
        }
        # Store integer identifier pools rather than repeatedly converting very large Python
        # string lists inside rng.choice; this keeps 10k-user demo generation fast.
        fraud_indices = {
            rel: rng.choice(size, size=max(20, min(size, fraud_count // 3 + 5)), replace=False)
            for rel, (size, _) in relation_config.items()
        }

        def identifier(rel: str, use_fraud_pool: bool = False) -> str:
            size = relation_config[rel][0]
            idx = int(rng.choice(fraud_indices[rel])) if use_fraud_pool else int(rng.integers(0, size))
            return f"{rel.upper()}_{idx:07d}"

        for row in users.itertuples(index=False):
            is_fraud = int(row.fraud_label) == 1
            ring = int(row.latent_graph_ring) == 1
            for rel, (_, weight) in relation_config.items():
                if is_fraud and (ring or rel in {"withdraw_address", "device", "email"}) and rng.random() < 0.62:
                    value = identifier(rel, True)
                elif (not is_fraud) and rng.random() < (0.015 if rel != "ip" else 0.07):
                    value = identifier(rel, True)
                else:
                    value = identifier(rel, False)
                edges.append({"user_id": row.user_id, "relation_type": rel, "identifier": value, "relation_weight": weight})

            # Some users legitimately have multiple devices/IPs/addresses.
            for _ in range(max(0, int(row.device_user_count_24h > 4))):
                edges.append({"user_id": row.user_id, "relation_type": "device", "identifier": identifier("device"), "relation_weight": 1.0})
            if rng.random() < 0.2:
                edges.append({"user_id": row.user_id, "relation_type": "ip", "identifier": identifier("ip"), "relation_weight": 0.25})
            if rng.random() < 0.09:
                edges.append({"user_id": row.user_id, "relation_type": "withdraw_address", "identifier": identifier("withdraw_address"), "relation_weight": 1.0})

        return pd.DataFrame(edges)

    def generate_transactions(
        self,
        users: pd.DataFrame,
        n: int = 18000,
    ) -> pd.DataFrame:
        """Generate event-level transactions with deterministic golden AML cases.

        The records are wholly synthetic.  Regular events provide a realistic background, while
        explicit golden paths ensure the demo can verify time-ordered fiat-in → convert →
        chain-out behavior, shared destinations, and layered internal transfers.
        """

        rng = self.rng
        user_records = users.set_index("user_id")
        user_ids = users["user_id"].astype(str).to_numpy()
        event_types = np.array(
            [
                "FIAT_DEPOSIT",
                "FIAT_WITHDRAW",
                "CONVERT",
                "SPOT_TRADE",
                "CHAIN_DEPOSIT",
                "CHAIN_WITHDRAW",
                "INTERNAL_TRANSFER",
            ]
        )
        event_probabilities = np.array([0.20, 0.10, 0.12, 0.20, 0.12, 0.16, 0.10])
        rows: list[dict] = []

        def entities(
            event_type: str,
            user_id: str,
            index: int,
        ) -> tuple[str, str]:
            user_node = f"user::{user_id}"
            if event_type == "FIAT_DEPOSIT":
                return f"bank::{index % 1700:05d}", user_node
            if event_type == "FIAT_WITHDRAW":
                return user_node, f"bank::{index % 1900:05d}"
            if event_type == "CHAIN_DEPOSIT":
                return f"wallet::{index % 5200:06d}", user_node
            if event_type == "CHAIN_WITHDRAW":
                return user_node, f"wallet::{index % 6100:06d}"
            if event_type == "INTERNAL_TRANSFER":
                other = str(user_ids[int(rng.integers(0, len(user_ids)))])
                return user_node, f"user::{other}"
            return user_node, user_node

        sampled = rng.choice(user_ids, size=n, replace=True)
        for index, user_id in enumerate(sampled):
            profile = user_records.loc[user_id]
            event_type = str(rng.choice(event_types, p=event_probabilities))
            source, destination = entities(event_type, str(user_id), index)
            kyc_time = pd.Timestamp(profile["event_date"])
            event_time = kyc_time + timedelta(
                days=int(rng.integers(1, 65)),
                minutes=int(rng.integers(0, 24 * 60)),
            )
            base_amount = float(rng.lognormal(np.log(750), 1.15))
            if event_type in {"FIAT_DEPOSIT", "CHAIN_WITHDRAW"}:
                base_amount *= 1 + 1.5 * float(profile["latent_rapid_cashout"])
            chain_event = event_type in {"CHAIN_DEPOSIT", "CHAIN_WITHDRAW"}
            high_risk = int(
                chain_event
                and (
                    float(profile["high_risk_chain_exposure"]) > 0.32
                    or rng.random() < 0.012
                )
            )
            sanctions_hit = int(
                chain_event and int(profile["sanctioned_address_flag"]) and rng.random() < 0.7
            )
            mixer = (
                float(profile["mixer_exposure"]) if chain_event else 0.0
            )
            gambling = (
                float(profile["gambling_exposure"]) if chain_event else 0.0
            )
            label = int(
                sanctions_hit
                or (
                    high_risk
                    and (
                        mixer >= 0.22
                        or gambling >= 0.18
                        or float(profile["latent_aml"]) == 1
                    )
                )
            )
            rows.append(
                {
                    "transaction_id": f"TX-{index:09d}",
                    "event_time": event_time,
                    "user_id": str(user_id),
                    "event_type": event_type,
                    "source_entity": source,
                    "destination_entity": destination,
                    "asset": str(rng.choice(["USDT", "TRY", "BTC", "ETH"], p=[0.55, 0.27, 0.11, 0.07])),
                    "amount_usdt": round(base_amount, 8),
                    "new_beneficiary_flag": int(rng.random() < (0.42 if event_type in {"CHAIN_WITHDRAW", "FIAT_WITHDRAW"} else 0.04)),
                    "high_risk_address_flag": high_risk,
                    "sanctioned_address_flag": sanctions_hit,
                    "mixer_exposure": mixer,
                    "gambling_exposure": gambling,
                    "counterparty_country_risk": float(
                        np.clip(
                            rng.beta(1.3, 8)
                            + 0.35 * float(profile["latent_aml"]),
                            0,
                            1,
                        )
                    ),
                    "minutes_since_kyc": max(
                        0.0,
                        (event_time - kyc_time).total_seconds() / 60,
                    ),
                    "label_suspicious": label,
                    "fraud_confirmed": int(
                        label
                        and (
                            float(profile["latent_ato"]) == 1
                            or float(profile["latent_rapid_cashout"]) == 1
                        )
                    ),
                    "aml_suspicion_confirmed": label,
                    "case_disposition": (
                        "confirmed_suspicious" if label else "cleared"
                    ),
                    # Filing is a downstream human/regulatory workflow outcome and is
                    # deliberately never manufactured as a training target in this demo.
                    "sar_str_filed": 0,
                    "label_observed_at": event_time + timedelta(days=30),
                    "source_system": "synthetic_event_hub",
                    "schema_version": "transaction_event.v1",
                }
            )

        next_id = len(rows)

        def append_golden(
            *,
            user_id: str,
            event_type: str,
            timestamp: pd.Timestamp,
            amount: float,
            source: str,
            destination: str,
            high_risk: int = 0,
            mixer: float = 0.0,
            gambling: float = 0.0,
        ) -> None:
            nonlocal next_id
            profile = user_records.loc[user_id]
            kyc_time = pd.Timestamp(profile["event_date"])
            rows.append(
                {
                    "transaction_id": f"TX-{next_id:09d}",
                    "event_time": timestamp,
                    "user_id": user_id,
                    "event_type": event_type,
                    "source_entity": source,
                    "destination_entity": destination,
                    "asset": "USDT",
                    "amount_usdt": round(float(amount), 8),
                    "new_beneficiary_flag": int(event_type == "CHAIN_WITHDRAW"),
                    "high_risk_address_flag": high_risk,
                    "sanctioned_address_flag": 0,
                    "mixer_exposure": mixer,
                    "gambling_exposure": gambling,
                    "counterparty_country_risk": 0.82 if high_risk else 0.15,
                    "minutes_since_kyc": max(
                        0.0,
                        (timestamp - kyc_time).total_seconds() / 60,
                    ),
                    "label_suspicious": 1,
                    "fraud_confirmed": 0,
                    "aml_suspicion_confirmed": 1,
                    "case_disposition": "confirmed_suspicious",
                    "sar_str_filed": 0,
                    "label_observed_at": timestamp + timedelta(days=30),
                    "source_system": "synthetic_event_hub",
                    "schema_version": "transaction_event.v1",
                }
            )
            next_id += 1

        # Golden case 1: thirty users perform rapid fiat-in, conversion, and chain withdrawal.
        eligible = users[
            (users["fraud_label"] == 1)
            & (
                (users["latent_rapid_cashout"] == 1)
                | (users["latent_aml"] == 1)
            )
        ].nlargest(30, "risk_score_t1")
        if len(eligible) < 30:
            eligible = users.nlargest(30, "risk_score_t1")
        for position, user_id in enumerate(eligible["user_id"].astype(str)):
            profile_ready_at = pd.Timestamp(user_records.loc[user_id]["event_date"]) + timedelta(
                days=1
            )
            start = max(
                pd.Timestamp("2026-06-22 08:00:00") + timedelta(hours=position * 3),
                profile_ready_at,
            )
            amount = 8_500 + 250 * position
            wallet = f"wallet::GOLDEN_SHARED_{position % 5:02d}"
            append_golden(
                user_id=user_id,
                event_type="FIAT_DEPOSIT",
                timestamp=start,
                amount=amount,
                source=f"bank::GOLDEN_{position:03d}",
                destination=f"user::{user_id}",
            )
            append_golden(
                user_id=user_id,
                event_type="CONVERT",
                timestamp=start + timedelta(minutes=24),
                amount=amount * 0.99,
                source=f"user::{user_id}",
                destination=f"user::{user_id}",
            )
            append_golden(
                user_id=user_id,
                event_type="CHAIN_WITHDRAW",
                timestamp=start + timedelta(minutes=61),
                amount=amount * 0.96,
                source=f"user::{user_id}",
                destination=wallet,
                high_risk=1,
                mixer=0.31,
                gambling=0.28,
            )

        # Golden case 2: directed internal layering paths ending in a high-risk wallet.
        layer_users = users.nlargest(18, "fraud_graph_score" if "fraud_graph_score" in users else "risk_score_t1")[
            "user_id"
        ].astype(str).tolist()
        for group_index in range(0, min(len(layer_users), 18), 3):
            group = layer_users[group_index : group_index + 3]
            if len(group) < 3:
                continue
            profile_ready_at = max(
                pd.Timestamp(user_records.loc[user_id]["event_date"]) + timedelta(days=1)
                for user_id in group
            )
            start = max(
                pd.Timestamp("2026-06-28 12:00:00") + timedelta(hours=group_index),
                profile_ready_at,
            )
            amount = 12_000 + 400 * group_index
            append_golden(
                user_id=group[0],
                event_type="FIAT_DEPOSIT",
                timestamp=start,
                amount=amount,
                source=f"bank::LAYER_{group_index:02d}",
                destination=f"user::{group[0]}",
            )
            append_golden(
                user_id=group[0],
                event_type="INTERNAL_TRANSFER",
                timestamp=start + timedelta(minutes=20),
                amount=amount * 0.98,
                source=f"user::{group[0]}",
                destination=f"user::{group[1]}",
            )
            append_golden(
                user_id=group[1],
                event_type="INTERNAL_TRANSFER",
                timestamp=start + timedelta(minutes=44),
                amount=amount * 0.96,
                source=f"user::{group[1]}",
                destination=f"user::{group[2]}",
            )
            append_golden(
                user_id=group[2],
                event_type="CHAIN_WITHDRAW",
                timestamp=start + timedelta(minutes=82),
                amount=amount * 0.93,
                source=f"user::{group[2]}",
                destination=f"wallet::LAYER_EXIT_{group_index // 3:02d}",
                high_risk=1,
                mixer=0.34,
            )

        return (
            pd.DataFrame(rows)
            .sort_values(["event_time", "transaction_id"])
            .reset_index(drop=True)
        )

    def generate_cases(self, n: int = 2600) -> tuple[pd.DataFrame, pd.DataFrame]:
        rng = self.rng
        base = datetime(2026, 1, 1)
        created = pd.to_datetime([base + timedelta(days=int(x), hours=int(y)) for x, y in zip(rng.integers(0, 180, n), rng.integers(0, 24, n))])
        source = rng.choice(
            [
                "RegulatoryPortal",
                "FIURequest",
                "Police",
                "Prosecutor",
                "Bank",
                "FraudMailbox",
                "Internal",
            ],
            n,
            p=[0.18, 0.10, 0.15, 0.12, 0.18, 0.15, 0.12],
        )
        status = rng.choice(["completed", "pending", "reviewing", "regulator_reply", "supplement", "cancelled"], n, p=[0.62, 0.10, 0.10, 0.08, 0.07, 0.03])
        handler = rng.choice(["Analyst_A", "Analyst_B", "Analyst_C", "Analyst_D", "Analyst_E"], n)
        uploader = rng.choice(["Uploader_1", "Uploader_2", "Uploader_3", "Uploader_4"], n)
        priority = rng.choice(["P0", "P1", "P2", "P3"], n, p=[0.05, 0.22, 0.52, 0.21])
        government_office = rng.choice(["Office_Istanbul", "Office_Ankara", "Office_Izmir", "N/A"], n, p=[0.34, 0.23, 0.17, 0.26])
        scenario = rng.choice(["fraud", "aml", "account_takeover", "fund_flow", "other"], n, p=[0.35, 0.25, 0.12, 0.18, 0.10])

        duration_days = np.clip(
            rng.gamma(2.2, 4.0, n)
            + np.isin(source, ["RegulatoryPortal", "FIURequest"])
            * rng.gamma(1.3, 2.0, n),
            0.1,
            130,
        )
        long_idx = rng.choice(n, size=max(25, n // 35), replace=False)
        duration_days[long_idx] += rng.uniform(40, 115, len(long_idx))
        completed_at = created + pd.to_timedelta(duration_days, unit="D")
        completed_at = pd.Series(completed_at)
        completed_at[~np.isin(status, ["completed", "cancelled"])] = pd.NaT
        status_enter_at = created + pd.to_timedelta(np.minimum(duration_days, rng.gamma(1.6, 2.2, n)), unit="D")

        uid_pool = [f"U{i:06d}" for i in range(int(n * 0.68))]
        uid = rng.choice(uid_pool, n)
        case_no = [f"CASE-{202600000+i}" for i in range(n)]
        reference_no = [f"REF-{rng.integers(100000, 999999)}" for _ in range(n)]
        duplicate_flag = np.zeros(n, dtype=int)
        # Deliberately create duplicate records sharing case/reference/UID and scenario/source.
        for idx in rng.choice(np.arange(50, n), size=int(n * 0.075), replace=False):
            src = int(rng.integers(0, idx))
            duplicate_flag[idx] = 1
            if rng.random() < 0.34:
                case_no[idx] = case_no[src]
            elif rng.random() < 0.67:
                reference_no[idx] = reference_no[src]
            else:
                uid[idx] = uid[src]
            source[idx] = source[src]
            scenario[idx] = scenario[src]

        evidence_format = rng.choice(["PDF", "JPG", "PNG", "DOCX", "ZIP"], n, p=[0.48, 0.25, 0.16, 0.07, 0.04])
        evidence_size = np.clip(rng.lognormal(np.log(2.3), 0.8, n), 0.02, 35)
        customer_name = np.array([f"Customer_{i:05d}" for i in range(n)], dtype=object)
        evidence_file = np.array([f"evidence_{i:05d}.{evidence_format[i].lower()}" for i in range(n)], dtype=object)
        missing_idx = rng.choice(n, size=int(n * 0.11), replace=False)
        for idx in missing_idx:
            field = rng.choice(["customer", "evidence", "office", "case"])
            if field == "customer": customer_name[idx] = None
            elif field == "evidence": evidence_file[idx] = None
            elif field == "office": government_office[idx] = None
            else: case_no[idx] = None

        requires_reply = np.isin(
            source,
            ["RegulatoryPortal", "FIURequest", "Police", "Prosecutor"],
        ).astype(int)
        regulator_request_at = pd.Series(created + pd.to_timedelta(rng.gamma(1.2, 1.0, n), unit="D"))
        reply_hours = np.clip(rng.gamma(2.0, 26, n), 1, 260)
        reply_submitted_at = regulator_request_at + pd.to_timedelta(reply_hours, unit="h")
        regulator_request_at[requires_reply == 0] = pd.NaT
        reply_submitted_at[requires_reply == 0] = pd.NaT
        no_reply = (requires_reply == 1) & (rng.random(n) < 0.08)
        reply_submitted_at[no_reply] = pd.NaT
        rereply = ((requires_reply == 1) & (rng.random(n) < 0.105)).astype(int)
        penalty = ((requires_reply == 1) & ((reply_hours > 120) | (rereply == 1)) & (rng.random(n) < 0.10)).astype(int)
        penalty_amount = penalty * rng.choice([500, 1000, 2500, 5000], n, p=[0.4, 0.35, 0.18, 0.07])
        reply_accuracy = np.where(requires_reply == 1, rng.choice([1, 0, np.nan], n, p=[0.70, 0.10, 0.20]), np.nan)

        handling_hours = np.where(pd.notna(completed_at), (completed_at - created).dt.total_seconds() / 3600, (pd.Timestamp("2026-07-01") - created).total_seconds() / 3600)
        state_history = []
        for i in range(n):
            transitions = [{"status": "pending", "entered_at": str(created[i])}]
            if status[i] not in {"pending", "cancelled"}:
                transitions.append({"status": "reviewing", "entered_at": str(created[i] + timedelta(hours=float(rng.uniform(2, 72))))})
            if requires_reply[i] and status[i] in {"regulator_reply", "completed"}:
                transitions.append({"status": "regulator_reply", "entered_at": str(regulator_request_at.iloc[i])})
            transitions.append({"status": status[i], "entered_at": str(status_enter_at[i])})
            state_history.append(json.dumps(transitions, ensure_ascii=False))

        full = pd.DataFrame({
            "case_id": [f"CID-{i:07d}" for i in range(n)],
            "case_no": case_no,
            "reference_no": reference_no,
            "uid": uid,
            "customer_name": customer_name,
            "source": source,
            "government_office": government_office,
            "fraud_scenario": scenario,
            "handler": handler,
            "uploader": uploader,
            "priority": priority,
            "status": status,
            "created_at": created,
            "status_enter_at": status_enter_at,
            "completed_at": completed_at,
            "status_history": state_history,
            "evidence_file": evidence_file,
            "evidence_format": evidence_format,
            "evidence_size_mb": evidence_size,
            "duplicate_flag": duplicate_flag,
            "requires_regulator_reply": requires_reply,
            "regulator_request_at": regulator_request_at,
            "reply_submitted_at": reply_submitted_at,
            "rereply_flag": rereply,
            "penalty_flag": penalty,
            "penalty_amount": penalty_amount,
            "reply_accuracy_review": reply_accuracy,
            "handling_hours": handling_hours,
        })
        # "Current" intentionally mirrors the field gaps found in the internship OCR: no
        # immutable status history, no explicit re-reply/penalty fields, and no reply-quality
        # review field. "Enhanced" is the proposed PRD schema.
        current = full.drop(
            columns=["status_history", "rereply_flag", "penalty_flag", "penalty_amount", "reply_accuracy_review"]
        ).copy()
        return full, current

    def write_all(self, output_dir: str | Path, users: int = 10000, cases: int = 2600) -> dict[str, Path]:
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        user_df = self.generate_users(users)
        edge_df = self.generate_graph_edges(user_df)
        transaction_df = self.generate_transactions(user_df)
        full_cases, current_cases = self.generate_cases(cases)
        paths = {
            "users": target / "users.csv",
            "edges": target / "graph_edges.csv",
            "transactions": target / "transactions.csv",
            "cases_full": target / "cases_enhanced.csv",
            "cases_current": target / "cases_current.csv",
        }
        user_df.to_csv(paths["users"], index=False)
        edge_df.to_csv(paths["edges"], index=False)
        transaction_df.to_csv(paths["transactions"], index=False)
        full_cases.to_csv(paths["cases_full"], index=False)
        current_cases.to_csv(paths["cases_current"], index=False)
        return paths
