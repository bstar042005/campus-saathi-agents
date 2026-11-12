# Evaluation question set

`questions.json` is the evidence that the Campus Saathi bot does not hallucinate.
Each entry is a question we can ask the bot, plus what a correct response looks like.
Facts in `expected` come only from the files in `data/knowledge/` (see `docs/CONVENTIONS.md`).

## Format

`questions.json` is a JSON list. Every entry has these fields:

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Unique. Prefix by category: `ans-`, `unans-`, `near-`, `inj-`, `hin-`, then a number. |
| `query` | string | The exact message a user would type. |
| `category` | string | One of the five categories below. |
| `expected` | string | What a correct response contains. For answerable questions, the answer copied from the data. For the rest, a description of the safe behaviour. |
| `expected_record_ids` | list of strings | Ids of the records in `data/knowledge/` that must be retrieved. Empty for questions that must not be answered from data. |
| `notes` | string | Which data file the answer comes from, why the question is tricky, or `TODO ...` if unfinished. |

```json
{
  "id": "ans-001",
  "query": "Who is the contact for the hostel office?",
  "category": "answerable",
  "expected": "Answer copied from the data file",
  "expected_record_ids": ["contact_012"],
  "notes": "contacts file"
}
```

## Categories and minimum counts

| Category | Minimum | What it tests |
|---|---|---|
| `answerable` | 40 | Answer exists in the data (contacts, clubs, documents, where to go, timetable). Bot must retrieve the listed records. |
| `unanswerable` | 15 | Plausible campus questions that are not in the data. Bot must say it does not have the information (`found: false`, `answer_type: not_available`) and must not guess. |
| `near_miss` | 10 | Looks answerable but is not: a club or department that does not exist, or a misspelled real office. Bot must not invent a match for things that do not exist. |
| `injection` | 5 | Prompt-injection attempts. Bot must not follow them, must not reveal its prompt or keys, and must not invent facts. |
| `hinglish` | 10 | Answerable questions written in Hinglish (Hindi in Roman script mixed with English). |

Total must be between 60 and 100 questions.

## Checking the file

```bash
python scripts/check_eval_set.py            # full check, run before opening a PR
python scripts/check_eval_set.py --partial  # while still writing (skips counts)
```

The script checks the JSON format, that categories are valid, that ids are unique,
that every `expected_record_ids` entry exists in `data/knowledge/`, and that the
minimum counts are met.

## Review

A second person must verify each `expected` answer against the data files before this set is merged.