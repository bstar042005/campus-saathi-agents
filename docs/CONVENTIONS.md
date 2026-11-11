Node IDs always refer to ids in data/campus_map.json.
Every knowledge record has: id, type, aliases (list), node_id (nullable), source (URL or document name), last_verified (YYYY-MM-DD).
Chat response contract (defined in Issue 4.1):

{
  "response": "text shown to the user",
  "found": true,
  "answer_type": "knowledge | navigation | link | not_available",
  "sources": [{"id": "contact_012", "title": "Hostel Warden Office", "url": "https://..."}],
  "links": [{"label": "Academic Calendar", "url": "https://..."}],
  "node_id": "library",
  "last_verified": "2026-10-01"
}

Rule for all code: the LLM never supplies facts, phone numbers, emails or URLs on its own. They come only from the data files.
