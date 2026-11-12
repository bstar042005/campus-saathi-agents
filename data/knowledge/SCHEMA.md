
# Campus Knowledge Data Schema

This directory stores structured campus information used by the Campus Saathi agent.

All records must follow the common fields and the corresponding record-specific schema.

## 1. Common Fields

Every knowledge record must contain:

| Field | Type | Required | Description |
|---|---|---|---|
| id | string | Yes | Unique record identifier |
| type | string | Yes | Record type |
| aliases | array of strings | Yes | Alternative names, including Hindi/Hinglish terms |
| node_id | string or null | Yes | ID from data/campus_map.json, or null |
| source | string | Yes | Source URL or document name |
| last_verified | YYYY-MM-DD | Yes | Date when information was last verified |

## 2. Contacts — contacts.json

Stores information about campus offices and contact persons.

Additional fields:

| Field | Type | Required |
|---|---|---|
| name | string | Yes |
| office | string | Yes |
| phone | string or null | No |
| email | string or null | No |
| location_text | string | Yes |
| hours | string or null | No |

Example:

```json
{
  "id": "contact_test_001",
  "type": "contact",
  "aliases": ["Test Office", "परीक्षण कार्यालय"],
  "node_id": "office",
  "source": "TEST DATA",
  "last_verified": "2026-11-12",
  "name": "Test Contact",
  "office": "Test Office",
  "phone": null,
  "email": null,
  "location_text": "Test Location",
  "hours": null
}
```

## 3. Clubs — clubs.json

Stores information about campus clubs and societies.

Additional fields:

| Field | Type | Required |
|---|---|---|
| name | string | Yes |
| category | string | Yes |
| description | string | Yes |
| how_to_join | string | Yes |
| contact_id | string or null | No |

`contact_id`, when provided, must reference an existing contact record.

Example:

```json
{
  "id": "club_test_001",
  "type": "club",
  "aliases": ["Test Club", "परीक्षण क्लब"],
  "node_id": null,
  "source": "TEST DATA",
  "last_verified": "2026-11-12",
  "name": "Test Club",
  "category": "Technical",
  "description": "Dummy club record for schema testing.",
  "how_to_join": "Contact the test office.",
  "contact_id": "contact_test_001"
}
```

## 4. FAQs — faqs.json

Stores frequently asked campus-related questions.

Additional fields:

| Field | Type | Required |
|---|---|---|
| question | string | Yes |
| answer | string | Yes |
| required_documents | array of strings | Yes |
| category | string | Yes |
| related_step | string or null | No |

`related_step`, when provided, must match a key in data/steps.json.

Example:

```json
{
  "id": "faq_test_001",
  "type": "faq",
  "aliases": ["Test Question", "परीक्षण प्रश्न"],
  "node_id": "gate",
  "source": "TEST DATA",
  "last_verified": "2026-11-12",
  "question": "Where is the test entry point?",
  "answer": "This is a dummy answer for schema testing.",
  "required_documents": [],
  "category": "General",
  "related_step": "gate"
}
```

## 5. Official Links — official_links.json

Stores verified official website links.

Additional fields:

| Field | Type | Required |
|---|---|---|
| key | string | Yes |
| label | string | Yes |
| url | string | Yes |
| description | string | Yes |

URLs must use HTTPS.

Example:

```json
{
  "id": "link_test_001",
  "type": "official_link",
  "aliases": ["Test Link", "परीक्षण लिंक"],
  "node_id": null,
  "source": "TEST DATA",
  "last_verified": "2026-11-12",
  "key": "test_portal",
  "label": "Test Portal",
  "url": "https://example.com",
  "description": "Dummy link for schema testing."
}
```

## 6. Validation Rules

The validation script must check:

1. Every record follows its corresponding schema.
2. IDs are unique across all four files.
3. Every non-null node_id exists in data/campus_map.json.
4. Every non-null contact_id references an existing contact.
5. Every non-null related_step exists in data/steps.json.
6. last_verified is a valid ISO date and is not in the future.
7. Official links use HTTPS.
8. Errors identify the filename, record ID (when available), and reason.

## 7. Test Data

Records with `source: "TEST DATA"` are dummy records used for development and validation.

They must be replaced with verified campus information before production use.
