import json
import re
from pathlib import Path
from typing import Any, Optional

from backend.config import KNOWLEDGE_DIR


def classify(query: str) -> str:
    normalized = query.lower()

    if any(re.search(rf"\b{term}\b", normalized) for term in ("hi", "hello", "thanks")):
        return "greeting"

    if any(term in normalized for term in (
        "timetable",
        "time table",
        "calendar",
        "schedule",
        "exam date",
    )):
        return "link"

    if any(term in normalized for term in (
        "fastest",
        "shortest",
        "best route",
        "best path",
        "all procedures",
        "complete all",
        "order of procedures",
    )):
        return "navigation"

    return "knowledge"


def get_link_by_key(key: str, knowledge_dir: Optional[Path] = None) -> Optional[dict[str, Any]]:
    links_path = (knowledge_dir or KNOWLEDGE_DIR) / "links.json"
    try:
        with links_path.open("r", encoding="utf-8") as links_file:
            links = json.load(links_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None

    if not isinstance(links, list):
        return None

    return next(
        (link for link in links if isinstance(link, dict) and link.get("key") == key),
        None,
    )


def not_available_text(main_link: Optional[dict[str, Any]] = None) -> tuple[str, str]:
    main_link = main_link or get_link_by_key("main_website")
    main_url = main_link.get("url") if main_link else "https://www.iiitdmj.ac.in"
    return (
        "I don't have that information. Please check the official website "
        f"({main_url}) or contact the relevant office.",
        main_url,
    )
