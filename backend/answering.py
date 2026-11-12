import logging
from typing import Optional, Any
from pydantic import BaseModel
from backend.knowledge import KnowledgeBase, RetrievalResult

logger = logging.getLogger(__name__)


class AnswerResult(BaseModel):
    answer: str
    found: bool
    answer_type: str
    links: list[str] = []
    suggested_contact: Optional[dict[str, Any]] = None


def answer_knowledge_query(
    query: str,
    history: Optional[list[dict[str, Any]]] = None,
    kb: Optional[KnowledgeBase] = None,
) -> AnswerResult:

    if kb is None:
        kb = KnowledgeBase()

    retrieval: RetrievalResult = kb.retrieve(query)

    if not retrieval.has_match:
        logger.info(
            "Hard gate triggered for query: '%s' (top score: %.4f). Returning standard 'not_available' response.",
            query,
            retrieval.top_score,
        )

        # Extract main website URL from links/official links
        main_url = "https://www.iiitdmj.ac.in"
        for rec in kb.records:
            if getattr(rec, "key", None) == "main_website" and hasattr(rec, "url"):
                main_url = rec.url
                break

        answer_text = (
            "I don't have that information. Please check the official website "
            f"({main_url}) or contact the relevant office."
        )

        suggested_contact = None
        q_lower = query.lower()
        keyword_to_contact_hint = {
            "fee": ["fee", "accounts", "shulk", "payment"],
            "hostel": ["hostel", "room", "warden", "hall"],
            "library": ["library", "book", "pustakalaya"],
            "admission": ["admission", "counselling", "josaa"],
        }

        matched_hint_keys = [
            category
            for category, keywords in keyword_to_contact_hint.items()
            if any(kw in q_lower for kw in keywords)
        ]

        if matched_hint_keys:
            for rec in kb.records:
                if rec.type == "contact":
                    rec_search_str = f"{rec.name} {rec.office} {rec.id} {' '.join(rec.aliases)}".lower()
                    if any(hint in rec_search_str for hint in matched_hint_keys):
                        suggested_contact = rec.model_dump()
                        break

        return AnswerResult(
            answer=answer_text,
            found=False,
            answer_type="not_available",
            links=[main_url],
            suggested_contact=suggested_contact,
        )

    matched_links = [
        r.record.url
        for r in retrieval.matches
        if hasattr(r.record, "url") and r.record.url
    ]
    return AnswerResult(
        answer=f"Found relevant information for: {query}",
        found=True,
        answer_type="found",
        links=matched_links,
    )