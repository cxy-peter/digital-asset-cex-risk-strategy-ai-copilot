from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..config import load_yaml
from ..schemas import KnowledgeScenario


@dataclass
class KnowledgeHit:
    doc_id: str
    score: float
    title: str
    text: str
    metadata: dict[str, Any]


class HybridKnowledgeRetriever:
    """A local hybrid retriever for SOPs, feature/event catalogs and risk scenarios.

    The demo uses word and character TF-IDF to stay fully offline. The interface is intentionally
    compatible with replacing the vectorizer with an embedding service or vector database.
    """

    def __init__(self, scenario_path: str | Path, sop_dir: str | Path) -> None:
        self.scenario_path = Path(scenario_path)
        self.sop_dir = Path(sop_dir)
        self.documents: list[dict[str, Any]] = []
        self.word_vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=25000)
        self.char_vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1, max_features=30000)
        self.word_matrix = None
        self.char_matrix = None
        self._load()

    def _load(self) -> None:
        scenarios = [KnowledgeScenario.model_validate(item) for item in load_yaml(self.scenario_path)]
        for scenario in scenarios:
            text = "\n".join(
                [
                    scenario.definition,
                    "风险类型：" + "、".join(scenario.risk_types),
                    "黑灰产工具：" + "、".join(scenario.black_grey_tools),
                    "攻击偏好：" + "、".join(scenario.attack_preferences),
                    "特征表现：" + "、".join(scenario.manifestations),
                    "候选特征：" + "、".join(scenario.candidate_features),
                    "专家规则：" + "、".join(scenario.expert_rules),
                    "模型：" + "、".join(scenario.recommended_models),
                ]
            )
            metadata = scenario.model_dump(mode="json")
            metadata.update(
                {
                    "type": "scenario",
                    "source_path": str(self.scenario_path),
                }
            )
            self.documents.append(
                {
                    "doc_id": scenario.scenario_id,
                    "title": f"{scenario.industry}/{scenario.business_line}/{scenario.event_stage}",
                    "text": text,
                    "metadata": metadata,
                }
            )
        for path in sorted(self.sop_dir.glob("*.md")):
            self.documents.append(
                {
                    "doc_id": f"SOP::{path.stem}",
                    "title": path.stem,
                    "text": path.read_text(encoding="utf-8"),
                    "metadata": {
                        "type": "sop",
                        "path": str(path),
                        "source_path": str(path),
                        "filename": path.name,
                    },
                }
            )
        corpus = [f"{doc['title']}\n{doc['text']}" for doc in self.documents]
        self.word_matrix = self.word_vectorizer.fit_transform(corpus)
        self.char_matrix = self.char_vectorizer.fit_transform(corpus)

    def search(
        self,
        query: str,
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
        document_type: str | None = None,
    ) -> list[KnowledgeHit]:
        if not query.strip():
            return []
        word_q = self.word_vectorizer.transform([query])
        char_q = self.char_vectorizer.transform([query])
        score = 0.62 * cosine_similarity(word_q, self.word_matrix)[0] + 0.38 * cosine_similarity(char_q, self.char_matrix)[0]
        filters = filters or {}
        hits = []
        for idx in np.argsort(score)[::-1]:
            doc = self.documents[int(idx)]
            metadata = doc["metadata"]
            if document_type and metadata.get("type") != document_type:
                continue
            if any(metadata.get(key) != value for key, value in filters.items()):
                continue
            hits.append(KnowledgeHit(doc["doc_id"], float(score[idx]), doc["title"], doc["text"], metadata))
            if len(hits) >= top_k:
                break
        return hits

    def search_scenarios(
        self,
        query: str,
        top_k: int = 6,
        industry: str | None = None,
    ) -> list[KnowledgeHit]:
        """Retrieve risk scenarios without allowing SOP documents into the ranking."""

        filters = {"industry": industry} if industry else None
        return self.search(
            query,
            top_k=top_k,
            filters=filters,
            document_type="scenario",
        )

    def search_sops(self, query: str, top_k: int = 4) -> list[KnowledgeHit]:
        """Retrieve SOP documents independently from scenario metadata filters."""

        return self.search(query, top_k=top_k, document_type="sop")
