# Finding schema

Each finding has the following shape:

~~~json
{
  "id": "finding-001",
  "code": "META_AS_QUESTION",
  "severity": "blocker",
  "subject": "数学一",
  "entityType": "question",
  "entityId": "series-overview",
  "observed": "chapter_metadata was used as a Question source",
  "expected": "entityType=chapter_metadata must stay out of Question Bank",
  "evidence": [
    {
      "path": "records/sources.json",
      "locator": "sources[series-overview]",
      "detail": "entityType=chapter_metadata"
    }
  ],
  "layer": "source-classification",
  "repairOwner": "learn/source-classification",
  "status": "open"
}
~~~

Required fields are id, code, severity, subject, entityType, entityId, observed, expected, evidence, layer, and repairOwner. evidence must point to a real file, record, node, question, URL, or rendered location. status is open unless the audit is comparing a previously recorded finding.

## Common codes

Use existing domain validator codes when available, including META_AS_QUESTION, QUESTION_DUPLICATED, QUESTION_CARD_MISMATCH, MATH_CONTENT_LOSS, RELATION_MISSING_TYPE, EMPTY_BRIDGE, and rendering or retrieval failures. Use a new code only when the existing contract cannot express the finding.
