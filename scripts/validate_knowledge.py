
import json
import sys
from pathlib import Path

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.knowledge_schema import Contact, Club, FaqEntry, OfficialLink


KNOWLEDGE_DIR = ROOT / "data" / "knowledge"
CAMPUS_MAP_FILE = ROOT / "data" / "campus_map.json"
STEPS_FILE = ROOT / "data" / "steps.json"

FILE_MODELS = {
    "contacts.json": Contact,
    "clubs.json": Club,
    "faqs.json": FaqEntry,
    "links.json": OfficialLink,
}


def load_json(path):
    """Load JSON data and report file errors."""
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        print(f"ERROR | {path.name} | {error}")
        return None


def validate_knowledge():
    errors = []
    records = []
    all_ids = {}
    contact_ids = set()


    campus_data = load_json(CAMPUS_MAP_FILE)
    if not isinstance(campus_data, dict) or not isinstance(
        campus_data.get("nodes"), dict
    ):
        errors.append("campus_map.json: missing or invalid 'nodes' object")
        campus_nodes = set()
    else:
        campus_nodes = set(campus_data["nodes"].keys())


    steps_data = load_json(STEPS_FILE)
    if not isinstance(steps_data, dict):
        errors.append("steps.json: expected a JSON object")
        step_keys = set()
    else:
        step_keys = set(steps_data.keys())

    for filename, model in FILE_MODELS.items():
        path = KNOWLEDGE_DIR / filename
        data = load_json(path)

        if data is None:
            errors.append(f"{filename}: could not load file")
            continue

        if not isinstance(data, list):
            errors.append(f"{filename}: expected a JSON array of records")
            continue

        for index, record in enumerate(data):
            if not isinstance(record, dict):
                errors.append(
                    f"{filename} | record #{index + 1}: expected a JSON object"
                )
                continue

            record_id = record.get("id", f"record #{index + 1}")

            if isinstance(record.get("id"), str):
                current_id = record["id"]
                if current_id in all_ids:
                    errors.append(
                        f"{filename} | {current_id}: duplicate ID; "
                        f"already exists in {all_ids[current_id]}"
                    )
                else:
                    all_ids[current_id] = filename

            if filename == "contacts.json" and isinstance(
                record.get("id"), str
            ):
                contact_ids.add(record["id"])

            try:
                validated_record = model.model_validate(record)
                records.append((filename, record_id, validated_record))

            except ValidationError as error:
                for issue in error.errors():
                    field = ".".join(str(part) for part in issue["loc"])
                    reason = issue["msg"]

                    errors.append(
                        f"{filename} | {record_id} | {field}: {reason}"
                    )

    for filename, record_id, record in records:

        if record.node_id is not None and record.node_id not in campus_nodes:
            errors.append(
                f"{filename} | {record_id}: "
                f"unknown node_id '{record.node_id}'"
            )

        if isinstance(record, Club):
            if (
                record.contact_id is not None
                and record.contact_id not in contact_ids
            ):
                errors.append(
                    f"{filename} | {record_id}: "
                    f"unknown contact_id '{record.contact_id}'"
                )

        if isinstance(record, FaqEntry):
            if (
                record.related_step is not None
                and record.related_step not in step_keys
            ):
                errors.append(
                    f"{filename} | {record_id}: "
                    f"unknown related_step '{record.related_step}'"
                )

    print("\n========== KNOWLEDGE VALIDATION ==========")

    if errors:
        print(f"\nValidation failed: {len(errors)} error(s) found.\n")

        for error in errors:
            print(f"ERROR: {error}")

        return False

    print("\nAll knowledge records are valid!")
    print(f"Validated {len(records)} record(s) across {len(FILE_MODELS)} files.")
    print("All IDs and cross-file references are valid.")

    return True


if __name__ == "__main__":
    success = validate_knowledge()
    sys.exit(0 if success else 1)
