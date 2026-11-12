import json
import re
from pathlib import Path
from typing import Any, Optional, Sequence

from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi
import logging
from backend.config import KNOWLEDGE_DIR, MIN_SCORE
from backend.knowledge_schema import (
    Club,
    Contact,
    FaqEntry,
    KnowledgeBase as KnowledgeRecord,
    OfficialLink,
)

FILE_MODELS: dict[str, type[KnowledgeRecord]] = {
    "contacts.json": Contact,
    "clubs.json": Club,
    "faqs.json": FaqEntry,
    "links.json": OfficialLink,
}

STOP_WORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "is", "are", "was", "were", "am", "be", "been", "being",
        "in", "on", "at", "to", "for", "of", "with", "by", "from", "about", "into",
        "and", "or", "but", "if", "so", "than", "that", "this", "these", "those",
        "it", "its", "my", "your", "our", "their", "i", "me", "we", "you", "he",
        "she", "they", "what", "which", "who", "whom", "where", "when", "why", "how",
        "do", "does", "did", "can", "could", "will", "would", "shall", "should",
        "may", "might", "must", "have", "has", "had", "please", "tell", "give",
        "ka", "ki", "ke", "ko", "se", "me", "mein", "par", "pe", "tak",
        "hai", "hain", "ho", "tha", "thi", "the", "hoga", "hogi",
        "kya", "kab", "kahan", "kaha", "kaise", "kaun", "kis", "kisko", "kyu", "kyun",
        "aur", "ya", "bhi", "hi", "toh", "to", "na", "nahi", "nhi",
        "ek", "ye", "yeh", "wo", "woh", "iska", "uska", "apna",
        "batao", "bataiye", "batana", "chahiye", "milega", "milegi", "karna", "kare",
    }
)

BM25_SATURATION_K = 2.0


def normalize_text(text: str) -> list[str]:

    lowered = text.lower()
    cleaned = re.sub(r"[^\w\s]", " ", lowered, flags=re.UNICODE)
    tokens = cleaned.split()
    return [tok for tok in tokens if tok and tok not in STOP_WORDS]


def normalize_bm25_score(raw_score: float, k: float = BM25_SATURATION_K) -> float:
    clamped = max(0.0, float(raw_score))
    if clamped == 0.0:
        return 0.0
    return round(clamped / (clamped + k), 4)


def build_searchable_text(record: KnowledgeRecord) -> str:
    """Extract all text fields and aliases from a validated knowledge record."""
    parts: list[str] = list(record.aliases)

    # Collect all standard string fields across any knowledge record model
    for field_name in [
        "name", "office", "location_text", "hours",
        "category", "description", "how_to_join",
        "question", "answer", "key", "label", "url"
    ]:
        val = getattr(record, field_name, None)
        if isinstance(val, str) and val.strip():
            parts.append(val)

    if hasattr(record, "required_documents") and isinstance(record.required_documents, list):
        parts.extend([str(doc) for doc in record.required_documents if doc])

    return " ".join(parts)

logger = logging.getLogger(__name__)

class SearchResult(BaseModel):
    record: Any
    score: float = Field(ge=0.0, le=1.0)
    record_type: str

class RetrievalResult(BaseModel):
    matches: list[SearchResult]
    top_score: float
    has_match: bool
class KnowledgeBase:

    def __init__(self, knowledge_dir: Path = KNOWLEDGE_DIR) -> None:
        self.knowledge_dir = Path(knowledge_dir)
        self.records: list[KnowledgeRecord] = []
        self._tokenized_corpus: list[list[str]] = []
        self._bm25: Optional[BM25Okapi] = None

        self._load_and_validate()
        self._build_index()

    def _load_and_validate(self) -> None:
        if not self.knowledge_dir.exists():
            raise FileNotFoundError(f"Knowledge directory not found: {self.knowledge_dir}")

        seen_ids: set[str] = set()
        loaded_records: list[KnowledgeRecord] = []

        for filename, model_cls in FILE_MODELS.items():
            file_path = self.knowledge_dir / filename
            if not file_path.exists():
                raise FileNotFoundError(f"Missing required knowledge file: {file_path}")

            with file_path.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if not isinstance(raw_data, list):
                raise ValueError(f"{filename} must contain a JSON list of records.")

            for idx, item in enumerate(raw_data):
                try:
                    record = model_cls.model_validate(item)
                except Exception as exc:
                    rec_id = item.get("id", f"index {idx}") if isinstance(item, dict) else f"index {idx}"
                    raise ValueError(f"Validation error in {filename} ({rec_id}): {exc}") from exc

                if record.id in seen_ids:
                    raise ValueError(f"Duplicate record ID '{record.id}' found in {filename}")
                seen_ids.add(record.id)
                loaded_records.append(record)

        self.records = loaded_records

    def _build_index(self) -> None:
        self._tokenized_corpus = [
            normalize_text(build_searchable_text(record)) for record in self.records
        ]
        if self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)

    def search(
        self,
        query: str,
        k: int = 3,
        types: Optional[Sequence[str]] = None,
    ) -> list[SearchResult]:
        if k <= 0 or not self.records or self._bm25 is None:
            return []

        query_tokens = normalize_text(query)
        allowed_types = set(types) if types is not None else None

        if not query_tokens:
            return []

        raw_scores = self._bm25.get_scores(query_tokens)

        results: list[SearchResult] = []
        for record, raw_score in zip(self.records, raw_scores):
            if allowed_types is not None and record.type not in allowed_types:
                continue

            norm_score = normalize_bm25_score(float(raw_score))
            results.append(
                SearchResult(
                    record=record,
                    score=norm_score,
                    record_type=record.type,
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:k]

    def retrieve(
        self,
        query: str,
        k: int = 3,
        types: Optional[Sequence[str]] = None,
        min_score: float = MIN_SCORE,
    ) -> RetrievalResult:
        raw_results = self.search(query, k=k, types=types)
        top_score = raw_results[0].score if raw_results else 0.0
        
        filtered_matches = [r for r in raw_results if r.score >= min_score]
        has_match = len(filtered_matches) > 0

        logger.info(
            "Retrieval Decision | Query: '%s' | Top Score: %.4f | Threshold: %.4f | Has Match: %s | Matches Retained: %d",
            query,
            top_score,
            min_score,
            has_match,
            len(filtered_matches),
        )

        return RetrievalResult(
            matches=filtered_matches,
            top_score=top_score,
            has_match=has_match,
        )