import json
from unittest.mock import MagicMock
from backend.answering import answer_knowledge_query
from backend.knowledge import KnowledgeBase
from tests.test_knowledge_search import sample_knowledge_dir


def test_valid_llm_json_passes(monkeypatch, sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)

    mock_llm = MagicMock(
        return_value=json.dumps({
            "answer": "The Central Library is open from 09:00 to 22:00, Monday to Saturday.",
            "used_record_ids": ["contact_lib"],
            "found": True,
        })
    )
    monkeypatch.setattr("backend.answering.generate_structured_rag_response", mock_llm)

    result = answer_knowledge_query("What are the library hours?", kb=kb)

    assert result.found is True
    assert result.answer_type == "grounded_rag"
    assert result.used_record_ids == ["contact_lib"]
    assert "09:00 to 22:00" in result.answer
    assert mock_llm.call_count == 1


def test_malformed_json_retries_once_then_falls_back(monkeypatch, sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)

    mock_llm = MagicMock(return_value="Not valid JSON at all {{{")
    monkeypatch.setattr("backend.answering.generate_structured_rag_response", mock_llm)

    result = answer_knowledge_query("What are the library hours?", kb=kb)

    assert mock_llm.call_count == 2
    assert result.found is False
    assert result.answer_type == "not_available"
    assert "I don't have that information" in result.answer


def test_malformed_json_recovers_on_retry(monkeypatch, sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)

    valid_payload = json.dumps({
        "answer": "You can pay fees on the Online Fee Payment Portal.",
        "used_record_ids": ["link_fees"],
        "found": True,
    })
    mock_llm = MagicMock(side_effect=["{broken_json", valid_payload])
    monkeypatch.setattr("backend.answering.generate_structured_rag_response", mock_llm)

    result = answer_knowledge_query("How do I pay semester fees?", kb=kb)

    assert mock_llm.call_count == 2
    assert result.found is True
    assert result.used_record_ids == ["link_fees"]
    assert result.links == ["https://fees.example.edu"]


def test_invented_record_id_is_rejected_and_falls_back(monkeypatch, sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)

    hallucinated_payload = json.dumps({
        "answer": "Call the Dean at 9999999999.",
        "used_record_ids": ["contact_invented_999"],
        "found": True,
    })
    mock_llm = MagicMock(return_value=hallucinated_payload)
    monkeypatch.setattr("backend.answering.generate_structured_rag_response", mock_llm)

    result = answer_knowledge_query("What are the library hours?", kb=kb)

    assert mock_llm.call_count == 2
    assert result.found is False
    assert result.answer_type == "not_available"


def test_llm_found_false_returns_standard_reply(monkeypatch, sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)

    not_found_payload = json.dumps({
        "answer": "The context does not mention cafeteria menu prices.",
        "used_record_ids": [],
        "found": False,
    })
    mock_llm = MagicMock(return_value=not_found_payload)
    monkeypatch.setattr("backend.answering.generate_structured_rag_response", mock_llm)

    result = answer_knowledge_query("What is the library canteen burger price?", kb=kb)

    assert mock_llm.call_count == 1
    assert result.found is False
    assert result.answer_type == "not_available"
    assert "I don't have that information" in result.answer