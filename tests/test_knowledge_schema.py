
import json

from scripts import validate_knowledge as validator


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def prepare_test_data(tmp_path, monkeypatch):
    """Create isolated knowledge files for each test."""

    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()

    campus_map = {
        "nodes": {
            "gate": {"cluster": "neutral", "type": "entry"},
            "office": {"cluster": "hostel", "type": "room"}
        },
        "edges": []
    }

    steps = {
        "gate": {"step_name": "Entry"},
        "office": {"step_name": "Office"}
    }

    contacts = [{
        "id": "contact_001",
        "type": "contact",
        "aliases": ["Test Office", "परीक्षण कार्यालय"],
        "node_id": "office",
        "source": "TEST DATA",
        "last_verified": "2026-11-12",
        "name": "Test Contact",
        "office": "Test Office",
        "phone": None,
        "email": None,
        "location_text": "Test Location",
        "hours": None
    }]

    clubs = [{
        "id": "club_001",
        "type": "club",
        "aliases": ["Test Club", "परीक्षण क्लब"],
        "node_id": None,
        "source": "TEST DATA",
        "last_verified": "2026-11-12",
        "name": "Test Club",
        "category": "Technical",
        "description": "Test description",
        "how_to_join": "Contact the office",
        "contact_id": "contact_001"
    }]

    faqs = [{
        "id": "faq_001",
        "type": "faq",
        "aliases": ["Test Question", "परीक्षण प्रश्न"],
        "node_id": "gate",
        "source": "TEST DATA",
        "last_verified": "2026-11-12",
        "question": "Where is the gate?",
        "answer": "This is a test answer.",
        "required_documents": [],
        "category": "General",
        "related_step": "gate"
    }]

    official_links = [{
        "id": "link_001",
        "type": "official_link",
        "aliases": ["Test Portal", "परीक्षण पोर्टल"],
        "node_id": None,
        "source": "TEST DATA",
        "last_verified": "2026-11-12",
        "key": "test_portal",
        "label": "Test Portal",
        "url": "https://example.com",
        "description": "Test link"
    }]

    write_json(tmp_path / "campus_map.json", campus_map)
    write_json(tmp_path / "steps.json", steps)

    write_json(knowledge_dir / "contacts.json", contacts)
    write_json(knowledge_dir / "clubs.json", clubs)
    write_json(knowledge_dir / "faqs.json", faqs)
    write_json(knowledge_dir / "links.json", official_links)

    monkeypatch.setattr(validator, "KNOWLEDGE_DIR", knowledge_dir)
    monkeypatch.setattr(
        validator, "CAMPUS_MAP_FILE", tmp_path / "campus_map.json"
    )
    monkeypatch.setattr(
        validator, "STEPS_FILE", tmp_path / "steps.json"
    )

    return contacts, clubs, faqs, official_links


def test_valid_records_pass(tmp_path, monkeypatch):
    prepare_test_data(tmp_path, monkeypatch)

    assert validator.validate_knowledge() is True


def test_duplicate_id_fails(tmp_path, monkeypatch, capsys):
    contacts, clubs, faqs, links = prepare_test_data(
        tmp_path, monkeypatch
    )

    clubs[0]["id"] = contacts[0]["id"]

    write_json(validator.KNOWLEDGE_DIR / "clubs.json", clubs)

    assert validator.validate_knowledge() is False
    assert "duplicate ID" in capsys.readouterr().out


def test_missing_source_fails(tmp_path, monkeypatch, capsys):
    contacts, _, _, _ = prepare_test_data(tmp_path, monkeypatch)

    del contacts[0]["source"]

    write_json(validator.KNOWLEDGE_DIR / "contacts.json", contacts)

    assert validator.validate_knowledge() is False
    assert "source" in capsys.readouterr().out


def test_invalid_node_id_fails(tmp_path, monkeypatch, capsys):
    _, _, faqs, _ = prepare_test_data(tmp_path, monkeypatch)

    faqs[0]["node_id"] = "unknown_location"

    write_json(validator.KNOWLEDGE_DIR / "faqs.json", faqs)

    assert validator.validate_knowledge() is False
    assert "unknown node_id" in capsys.readouterr().out


def test_malformed_date_fails(tmp_path, monkeypatch, capsys):
    contacts, _, _, _ = prepare_test_data(tmp_path, monkeypatch)

    contacts[0]["last_verified"] = "12-11-2026"

    write_json(validator.KNOWLEDGE_DIR / "contacts.json", contacts)

    assert validator.validate_knowledge() is False
    assert "last_verified" in capsys.readouterr().out


def test_http_url_fails(tmp_path, monkeypatch, capsys):
    _, _, _, links = prepare_test_data(tmp_path, monkeypatch)

    links[0]["url"] = "http://example.com"

    write_json(
        validator.KNOWLEDGE_DIR / "links.json", links
    )

    assert validator.validate_knowledge() is False
    assert "https://" in capsys.readouterr().out


def test_unknown_contact_id_fails(tmp_path, monkeypatch, capsys):
    _, clubs, _, _ = prepare_test_data(tmp_path, monkeypatch)

    clubs[0]["contact_id"] = "contact_does_not_exist"

    write_json(validator.KNOWLEDGE_DIR / "clubs.json", clubs)

    assert validator.validate_knowledge() is False
    assert "unknown contact_id" in capsys.readouterr().out


def test_every_step_has_a_procedure_faq():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    steps = json.loads((root / "data/steps.json").read_text())
    faqs = json.loads(
        (root / "data/knowledge/faqs.json").read_text()
    )

    related_steps = {
        faq.get("related_step")
        for faq in faqs
        if faq.get("related_step") is not None
    }

    missing = set(steps) - related_steps
    assert not missing, f"Steps without FAQs: {sorted(missing)}"
