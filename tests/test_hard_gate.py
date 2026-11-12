import json
import pytest
from unittest.mock import MagicMock
from backend.answering import answer_knowledge_query
from backend.knowledge import KnowledgeBase
from tests.test_knowledge_search import sample_knowledge_dir


def test_hard_gate_triggers_on_unanswerable_query(monkeypatch, sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)

    mock_llm = MagicMock(side_effect=RuntimeError("LLM should not be called on hard gate!"))
    monkeypatch.setattr("backend.answering.generate_structured_rag_response", mock_llm)

    query = "What is the weather on Mars?"
    result = answer_knowledge_query(query, kb=kb)

    assert result.found is False
    assert result.answer_type == "not_available"
    assert "I don't have that information" in result.answer
    assert len(result.links) == 1
    assert result.links[0].startswith("https://")

    mock_llm.assert_not_called()


def test_hard_gate_suggests_relevant_contact(monkeypatch,sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)
    
    mock_llm = MagicMock(
        return_value=json.dumps({
            "answer": "The Central Library helpdesk is on the Ground Floor.",
            "used_record_ids": ["contact_lib"],
            "found": True,
        })
    )
    monkeypatch.setattr("backend.answering.generate_structured_rag_response", mock_llm)

    query = "Where is the Central Library helpdesk located?"
    result = answer_knowledge_query(query, kb=kb)

    assert result.found is True
    assert result.answer_type == "grounded_rag"