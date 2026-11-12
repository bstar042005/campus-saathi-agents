import os
import json
import pytest
from backend.knowledge import KnowledgeBase, RetrievalResult

from tests.test_knowledge_search import sample_knowledge_dir

def test_valid_query_has_match(sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)
    result = kb.retrieve("Central Library", min_score=0.35)

    assert result.has_match is True
    assert result.top_score >= 0.20
    assert len(result.matches) > 0


def test_nonsense_query_returns_no_match(sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)
    result = kb.retrieve("What is the weather on Mars?", min_score=0.35)

    assert result.has_match is False
    assert result.top_score < 0.35
    assert len(result.matches) == 0


def test_env_var_kb_min_score_overrides_threshold(sample_knowledge_dir, monkeypatch):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)
    
    query = "pustakalaya"
    
    monkeypatch.setenv("KB_MIN_SCORE", "0.99")
    result_high = kb.retrieve(query, min_score=float(os.getenv("KB_MIN_SCORE")))
    assert result_high.has_match is False

    monkeypatch.setenv("KB_MIN_SCORE", "0.05")
    result_low = kb.retrieve(query, min_score=float(os.getenv("KB_MIN_SCORE")))
    assert result_low.has_match is True