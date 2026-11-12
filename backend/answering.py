import json
import logging
from typing import Optional, Any
from pydantic import BaseModel, ValidationError
from backend.knowledge import KnowledgeBase, RetrievalResult
from backend.prompts import KNOWLEDGE_SYSTEM_PROMPT, format_context_blocks
from backend.groq_service import generate_structured_rag_response

logger = logging.getLogger(__name__)


class LLMJsonReply(BaseModel):
    answer: str
    used_record_ids: list[str]
    found: bool

class AnswerResult(BaseModel):
    answer: str
    found: bool
    answer_type: str
    links: list[str] = []
    used_record_ids: list[str] = []
    suggested_contact: Optional[dict[str, Any]] = None



def _build_not_available_reply(query: str, kb: KnowledgeBase) -> AnswerResult:
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
        used_record_ids=[],
        suggested_contact=suggested_contact,
    )

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

        return _build_not_available_reply(query, kb)

    retrieved_records = [m.record for m in retrieval.matches]
    allowed_ids = {rec.id for rec in retrieved_records}
    records_by_id = {rec.id: rec for rec in retrieved_records}

    context_block = format_context_blocks(retrieved_records)
    user_prompt = f"Context Records:\n{context_block}\n\nUser Question: {query}"

    parsed_reply: Optional[LLMJsonReply] = None
    for attempt in range(2):
        raw_json_str = generate_structured_rag_response(
            system_prompt=KNOWLEDGE_SYSTEM_PROMPT,
            user_message=user_prompt,
            history=history,
        )
        try:
            data = json.loads(raw_json_str)
            candidate = LLMJsonReply.model_validate(data)

            invented_ids = set(candidate.used_record_ids) - allowed_ids
            if invented_ids:
                logger.warning(
                    "Attempt %d: LLM cited unretrieved record IDs %s (allowed: %s)",
                    attempt + 1,
                    invented_ids,
                    allowed_ids,
                )
                continue

            parsed_reply = candidate
            break
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("Attempt %d: LLM JSON validation failed: %s", attempt + 1, exc)

    if parsed_reply is None or not parsed_reply.found:
        logger.info("Falling back to 'not_available' for query: '%s'", query)
        return _build_not_available_reply(query, kb)

    used_links = [
        records_by_id[rid].url
        for rid in parsed_reply.used_record_ids
        if rid in records_by_id and getattr(records_by_id[rid], "url", None)
    ]

    return AnswerResult(
        answer=parsed_reply.answer,
        found=True,
        answer_type="grounded_rag",
        links=used_links,
        used_record_ids=parsed_reply.used_record_ids,
    )