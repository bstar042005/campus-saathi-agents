import json
import pytest
from backend.knowledge import KnowledgeBase, normalize_text


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def sample_knowledge_dir(tmp_path):
    """Create a small, isolated fixture knowledge base for deterministic search testing."""
    kdir = tmp_path / "knowledge"
    kdir.mkdir()

    contacts = [
        {
            "id": "contact_lib",
            "type": "contact",
            "aliases": ["Central Library", "pustakalaya", "kitab ghar"],
            "node_id": "library",
            "source": "TEST DATA",
            "last_verified": "2026-10-01",
            "name": "Central Library Helpdesk",
            "office": "Library Ground Floor",
            "phone": "+91-761-2632-000",
            "email": "library@example.edu",
            "location_text": "Central Library Building near Lecture Hall",
            "hours": "Mon-Sat 09:00 - 22:00",
        },
        {
            "id": "contact_hostel",
            "type": "contact",
            "aliases": ["Warden Office", "chhatravas"],
            "node_id": "hostel",
            "source": "TEST DATA",
            "last_verified": "2026-10-01",
            "name": "Chief Hostel Warden",
            "office": "Hall 1 Admin Room",
            "phone": None,
            "email": "warden@example.edu",
            "location_text": "Hostel Zone",
            "hours": "10:00 - 18:00",
        },
    ]

    clubs = [
        {
            "id": "club_astro",
            "type": "club",
            "aliases": ["Astronomy Club", "taara mandal", "stargazing society"],
            "node_id": "sac",
            "source": "TEST DATA",
            "last_verified": "2026-10-01",
            "name": "Astronomy and Physics Society",
            "category": "Science",
            "description": "Night sky observation sessions and telescope workshops.",
            "how_to_join": "Attend the orientation session in September.",
            "contact_id": "contact_lib",
        }
    ]

    faqs = [
        {
            "id": "faq_bonafide",
            "type": "faq",
            "aliases": ["bonafide certificate", "student proof"],
            "node_id": "admin",
            "source": "TEST DATA",
            "last_verified": "2026-10-01",
            "question": "How do I apply for a bonafide certificate?",
            "answer": "Submit the application form at the Academic Section with your ID card.",
            "required_documents": ["Institute ID Card"],
            "category": "Academics",
            "related_step": None,
        }
    ]

    official_links = [
        {
            "id": "link_fees",
            "type": "official_link",
            "aliases": ["fee payment", "semester fees", "shulk"],
            "node_id": None,
            "source": "TEST DATA",
            "last_verified": "2026-10-01",
            "key": "fee_portal",
            "label": "Online Fee Payment Portal",
            "url": "https://fees.example.edu",
            "description": "Pay semester tuition and hostel fees online.",
        }
    ]

    write_json(kdir / "contacts.json", contacts)
    write_json(kdir / "clubs.json", clubs)
    write_json(kdir / "faqs.json", faqs)
    write_json(kdir / "links.json", official_links)

    return kdir


def test_text_normalization_removes_punctuation_and_fillers():
    tokens = normalize_text("Bhai, Central Library ka timing kya hai?!")
    assert tokens == ["bhai", "central", "library", "timing"]


def test_exact_title_query_ranks_record_first(sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)
    results = kb.search("Astronomy and Physics Society", k=3)

    assert len(results) > 0
    assert results[0].record.id == "club_astro"
    assert results[0].record_type == "club"
    assert 0.0 < results[0].score <= 1.0


def test_alias_query_finds_record(sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)
    results = kb.search("pustakalaya hours", k=3)

    assert len(results) > 0
    assert results[0].record.id == "contact_lib"
    assert results[0].record_type == "contact"


def test_nonsense_query_returns_low_scores(sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)
    results = kb.search("xyzzy blargflorp quux", k=3)

    assert all(r.score == 0.0 for r in results)


def test_types_filter_restricts_results(sample_knowledge_dir):
    kb = KnowledgeBase(knowledge_dir=sample_knowledge_dir)
    results = kb.search("library", k=5, types=["club", "faq"])

    assert all(r.record_type in {"club", "faq"} for r in results)
    assert all(r.record.id != "contact_lib" for r in results)


def test_startup_fails_loudly_on_invalid_data(sample_knowledge_dir):
    bad_links = [
        {
            "id": "link_bad",
            "type": "official_link",
            "aliases": [],
            "node_id": None,
            "source": "TEST DATA",
            "last_verified": "2026-10-01",
            "key": "bad",
            "label": "Bad HTTP Link",
            "url": "http://insecure.example.edu",
            "description": "Invalid non-https URL",
        }
    ]
    write_json(sample_knowledge_dir / "links.json", bad_links)

    with pytest.raises(ValueError, match="links.json"):
        KnowledgeBase(knowledge_dir=sample_knowledge_dir)


def test_startup_fails_loudly_on_missing_directory(tmp_path):
    with pytest.raises(FileNotFoundError):
        KnowledgeBase(knowledge_dir=tmp_path / "does_not_exist")