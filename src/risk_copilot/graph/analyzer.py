from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable

import networkx as nx
import numpy as np
import pandas as pd


RELATION_STRENGTH = {
    "device": 1.0,
    "email": 0.85,
    "mobile": 0.95,
    "kyc_id": 1.0,
    "withdraw_address": 1.0,
    "ip": 0.25,
}


class RiskGraphAnalyzer:
    """Builds a bipartite user-identifier graph and derives auditable risk features.

    IP is intentionally down-weighted. Deposit addresses are not included by default because
    exchange aggregation addresses can create very large false-positive components.
    """

    def __init__(self, relation_strength: dict[str, float] | None = None) -> None:
        self.relation_strength = relation_strength or RELATION_STRENGTH
        self.graph = nx.Graph()
        self.user_labels: dict[str, int] = {}

    def fit(
        self,
        users: pd.DataFrame,
        edges: pd.DataFrame,
        known_label_user_ids: set[str] | None = None,
    ) -> "RiskGraphAnalyzer":
        self.graph.clear()
        labels = users.set_index("user_id")["fraud_label"].astype(int).to_dict()
        known = (
            {str(user_id) for user_id in known_label_user_ids}
            if known_label_user_ids is not None
            else None
        )
        self.user_labels = {
            str(user_id): int(label)
            for user_id, label in labels.items()
            if known is None or str(user_id) in known
        }
        for row in users[["user_id"]].itertuples(index=False):
            user_id = str(row.user_id)
            self.graph.add_node(
                user_id,
                node_type="user",
                fraud_label=self.user_labels.get(user_id),
                label_known=user_id in self.user_labels,
            )
        for row in edges.itertuples(index=False):
            relation = str(row.relation_type)
            if relation not in self.relation_strength:
                continue
            id_node = f"{relation}::{row.identifier}"
            self.graph.add_node(id_node, node_type="identifier", relation_type=relation)
            self.graph.add_edge(
                str(row.user_id),
                id_node,
                relation_type=relation,
                weight=float(getattr(row, "relation_weight", self.relation_strength[relation])),
            )
        return self

    def _neighbor_users_by_relation(self, user_id: str) -> dict[str, set[str]]:
        result: dict[str, set[str]] = defaultdict(set)
        if user_id not in self.graph:
            return result
        for identifier in self.graph.neighbors(user_id):
            relation = self.graph.nodes[identifier].get("relation_type", "unknown")
            for neighbor in self.graph.neighbors(identifier):
                if neighbor != user_id and self.graph.nodes[neighbor].get("node_type") == "user":
                    result[relation].add(neighbor)
        return result

    def user_features(self, user_id: str, max_hops: int = 2) -> dict[str, float | int]:
        relations = self._neighbor_users_by_relation(user_id)
        one_hop_fraud = {
            rel: sum(self.user_labels.get(u, 0) for u in users) for rel, users in relations.items()
        }
        strong_fraud = sum(
            count for rel, count in one_hop_fraud.items() if self.relation_strength.get(rel, 0) >= 0.8
        )
        weighted_one_hop = sum(
            self.relation_strength.get(rel, 0) * count for rel, count in one_hop_fraud.items()
        )

        # User-to-user projection is computed locally for the requested node to avoid materializing
        # a very dense full projection.
        first_users = set().union(*relations.values()) if relations else set()
        second_users: set[str] = set()
        if max_hops >= 2:
            for first in first_users:
                second_rel = self._neighbor_users_by_relation(first)
                for rel, users in second_rel.items():
                    if self.relation_strength.get(rel, 0) >= 0.8:
                        second_users.update(users)
            second_users.discard(user_id)
            second_users -= first_users
        two_hop_fraud = sum(self.user_labels.get(u, 0) for u in second_users)

        graph_score = 1 - np.exp(-(weighted_one_hop + 0.35 * two_hop_fraud))
        return {
            "device_fraud_1hop_count": int(one_hop_fraud.get("device", 0)),
            "withdraw_address_fraud_1hop_count": int(one_hop_fraud.get("withdraw_address", 0)),
            "email_fraud_1hop_count": int(one_hop_fraud.get("email", 0)),
            "mobile_fraud_1hop_count": int(one_hop_fraud.get("mobile", 0)),
            "kyc_id_fraud_1hop_count": int(one_hop_fraud.get("kyc_id", 0)),
            "ip_fraud_1hop_count": int(one_hop_fraud.get("ip", 0)),
            "strong_relation_fraud_1hop_count": int(strong_fraud),
            "fraud_2hop_count": int(two_hop_fraud),
            "fraud_graph_score": float(np.clip(graph_score, 0, 1)),
            "direct_related_user_count": int(len(first_users)),
            "second_hop_user_count": int(len(second_users)),
        }

    def transform(self, users: pd.DataFrame) -> pd.DataFrame:
        records = [self.user_features(uid) for uid in users["user_id"].astype(str)]
        feature_df = pd.DataFrame(records, index=users.index)
        enriched = users.copy()
        for column in feature_df.columns:
            enriched[column] = feature_df[column]
        # A lightweight proxy for community risk without an expensive global community algorithm.
        enriched["community_fraud_ratio"] = np.clip(
            enriched["strong_relation_fraud_1hop_count"]
            / np.maximum(enriched["direct_related_user_count"], 1),
            0,
            1,
        )
        return enriched

    def explain_user(self, user_id: str, max_neighbors: int = 20) -> dict:
        relations = self._neighbor_users_by_relation(user_id)
        paths = []
        for relation, users in relations.items():
            for neighbor in sorted(users)[:max_neighbors]:
                paths.append(
                    {
                        "source": user_id,
                        "relation": relation,
                        "target": neighbor,
                        "target_is_fraud": bool(self.user_labels.get(neighbor, 0)),
                        "strength": self.relation_strength.get(relation, 0),
                    }
                )
        return {"user_id": user_id, "features": self.user_features(user_id), "paths": paths}

    @classmethod
    def from_csv(cls, users_path: str | Path, edges_path: str | Path) -> "RiskGraphAnalyzer":
        users = pd.read_csv(users_path)
        edges = pd.read_csv(edges_path)
        return cls().fit(users, edges)
