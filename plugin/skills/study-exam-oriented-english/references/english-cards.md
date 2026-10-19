# English domain cards

English cards are Derived records. A card is a reusable language function or
diagnostic unit, not a whole essay template or an isolated word with no
independent learning value.

## Card types

- `expression-function`: express a reason, contrast, example, suggestion,
  change, conclusion, or other communicative function;
- `grammar-pattern`: a teachable grammar structure with conditions and a
  simple example;
- `writing-structure`: a paragraph or task move for an application letter or
  longer essay;
- `translation-pattern`: a repeatable way to unpack clauses, logic, or word
  order into natural Chinese;
- `error-pattern`: a recurring, evidence-backed user error with examples;
- `vocabulary-in-context`: a term whose meaning depends on the sentence or
  exam context;
- `sentence-bridge`: a small bridge from a Chinese meaning unit to an English
  expression the learner can independently reuse.

## Common shape

```json
{
  "id": "english-card-reason-001",
  "type": "expression-function",
  "title": "Express a reason simply",
  "function": "reason",
  "coreMeaning": "Give a clear reason for a recommendation.",
  "recallPrompt": "How can I give a simple reason?",
  "difficulty": "standard",
  "examples": ["This is important because it affects daily life."],
  "sourceRefs": [{"sourceId": "english-source-001", "locator": "paragraph-2"}],
  "derivedVersion": 1,
  "status": "ACTIVE"
}
```

Cards may contain several examples, but each card must retain one core
function. Long essays, full answer templates, and every individual word belong
in Source or Question records and are projected into cards only when they have
an independent recall purpose.
