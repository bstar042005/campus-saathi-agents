# Chat API Contract (`POST /api/chat`)

## Endpoint Overview
- **URL**: `/api/chat`
- **Method**: `POST`

---

## Response Schema (`ChatResponse`)
```json
{
  "response": "The Academic Section is located in Room 102, Administrative Block.",
  "found": true,
  "answer_type": "knowledge",
  "sources": [
    {
      "id": "contact_012",
      "title": "Academic Section Office",
      "url": "[https://erp.iiitdmj.ac.in](https://erp.iiitdmj.ac.in)"
    }
  ],
  "links": [
    {
      "label": "Institute ERP Portal",
      "url": "[https://erp.iiitdmj.ac.in](https://erp.iiitdmj.ac.in)"
    }
  ],
  "node_id": "admin_block",
  "last_verified": "2026-10-01"
}